import sys
import os
from collections import Counter
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

from app.db.session import SessionLocal
from app.models import Teacher, Course, Room, StudentGroup, TimeSlot, CourseType
from app.services.solver.data_wrapper import SolverDataWrapper
from app.services.solver.engine import TimetableSolver
from app.schemas.solver import SolverConfig

def test_solver():
    db = SessionLocal()
    try:
        teachers = db.query(Teacher).all()
        courses = db.query(Course).all()
        rooms = db.query(Room).all()
        groups = db.query(StudentGroup).all()
        slots = db.query(TimeSlot).all()
        
        print("\n--- DATA STATISTICS ---")
        print(f"Teachers: {len(teachers)}")
        print(f"Courses: {len(courses)}")
        print(f"Slots: {len(slots)}")
        print(f"Rooms: {len(rooms)}")
        
        # Teacher Load Analysis
        print("\n--- TEACHER LOAD ---")
        teacher_loads = {}
        for t in teachers:
            teacher_loads[t.id] = 0
            
        unassigned = 0
        total_demand = 0
        
        for c in courses:
            sessions = c.weekly_sessions or 4
            
            # Calculate load units (Batches vs Single)
            units = 1
            if c.course_type != CourseType.THEORY:
                 # It multiplies by number of batches if not specific batch
                 if not c.batch_id and c.student_group:
                     units = len(c.student_group.batches)
                     if units == 0: units = 1 # Safety
            
            load = sessions * units
            total_demand += load
            
            if c.teacher_id:
                teacher_loads[c.teacher_id] = teacher_loads.get(c.teacher_id, 0) + load
            else:
                unassigned += load

        print(f"Total Demand (Hours): {total_demand}")
        print(f"Unassigned Demand: {unassigned}")
        
        overloaded_teachers = 0
        for t in teachers:
            load = teacher_loads.get(t.id, 0)
            capacity = (t.max_weekly_hours or 40)
            status = "OK"
            if load > capacity:
                status = "OVERLOAD"
                overloaded_teachers += 1
            if load > 0:
                print(f"Teacher {t.name}: {load} / {capacity} hrs ({status})")
        
        if overloaded_teachers > 0:
            print(f"\n!!! CRITICAL: {overloaded_teachers} teachers are OVERLOADED. Infeasible.")
        
        if unassigned > 0:
            # If default solver treats unassigned as Single "None" Teacher -> Infeasible if > capacity
            print(f"!!! CRITICAL: {unassigned} hours unassigned. Solver might choke if treating as single resource.")

        print("\n--- SOLVER RUN ---")
        wrapper = SolverDataWrapper(teachers, courses, rooms, groups, slots)
        allocations = []
        for c in courses:
            if not c.student_group_id: continue
            batches = []
            if c.batch_id and c.batch: batches = [c.batch]
            elif c.course_type in [CourseType.LAB, CourseType.TUTORIAL] and c.student_group:
                batches = c.student_group.batches
            
            allocations.append({
                "course": c,
                "group_id": c.student_group_id,
                "batches": batches,
                "teacher_id": c.teacher_id,
                "sessions": c.weekly_sessions or 4
            })

        config = SolverConfig(max_time_seconds=60, enable_soft_constraints=False)
        solver = TimetableSolver(wrapper, config)
        solver.create_variables(allocations)
        solver.add_hard_constraints()
        
        print(f"Variables: {len(solver.vars)}")
        solution = solver.solve()
        print(f"Result: {solution.status}")
        print(f"Entries: {len(solution.entries)}")

    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_solver()

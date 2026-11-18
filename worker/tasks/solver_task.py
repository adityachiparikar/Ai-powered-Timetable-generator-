from worker.celery_app import celery_app
from app.db.session import SessionLocal
from app.models import Teacher, Course, Room, StudentGroup, TimeSlot, TimetableEntry
from app.services.solver.data_wrapper import SolverDataWrapper
from app.services.solver.engine import TimetableSolver
from app.schemas.solver import SolverConfig

@celery_app.task(bind=True, name="worker.tasks.solver_task.run_solver_task")
def run_solver_task(self, term: str, config_dict: dict = None):
    db = SessionLocal()
    from app.services.solver.logger import SolverLogger
    logger = SolverLogger(self.request.id)
    logs = []

    def log(message: str):
        logs.append(message)
        logger.log(message)

    try:
        # 1. Fetch Data
        log(f"Starting Solver for term: {term}")
        teachers = db.query(Teacher).all()
        courses = db.query(Course).all()
        rooms = db.query(Room).all()
        groups = db.query(StudentGroup).all()
        slots = db.query(TimeSlot).all() # Filter by term not implemented yet in model
        
        log(f"Fetched {len(teachers)} teachers, {len(courses)} courses, {len(rooms)} rooms, {len(groups)} divisions, {len(slots)} time slots.")
        lecture_rooms = [r for r in rooms if not r.is_lab and not r.is_tutorial_room]
        lab_rooms = [r for r in rooms if r.is_lab]
        tutorial_rooms = [r for r in rooms if r.is_tutorial_room]
        log(f"Room capacity: {len(lecture_rooms)} lecture rooms, {len(lab_rooms)} lab rooms, {len(tutorial_rooms)} tutorial rooms.")
        
        # 2. Build Wrapper
        wrapper = SolverDataWrapper(teachers, courses, rooms, groups, slots)
        
        # 3. Create Allocations 
        from app.models.course import CourseType
        allocations = []
        skipped_no_group = 0
        skipped_no_teacher = 0
        skipped_no_batches = 0
        no_room_courses = []
        session_demand = {"THEORY": 0, "LAB": 0, "TUTORIAL": 0}
        for c in courses:
            if not c.student_group_id:
                # Skip courses without assigned group for now
                skipped_no_group += 1
                continue
            if not c.teacher_id:
                skipped_no_teacher += 1
                continue
                
            # Determine target batches
            target_batches = []
            if c.course_type == CourseType.THEORY:
                # Theory courses apply to the whole group — no batches needed
                target_batches = []
            elif c.batch_id:
                # Explicit batch assignment (e.g. a specific teacher assigned to Batch A)
                if c.batch:
                    target_batches = [c.batch]
            else:
                # Lab/Tutorial with no explicit batch_id set.
                # Try to infer the target batch from the course code suffix.
                # Convention: course codes end with -B1, -B2, -B3 etc. (case-insensitive)
                # e.g. "ML101-A-L-B2" → batch name "b2"
                inferred_batch = None
                if c.student_group and c.student_group.batches and c.code:
                    code_parts = c.code.upper().split('-')
                    # Walk backwards through the code segments to find a batch name match
                    for segment in reversed(code_parts):
                        matched = next(
                            (b for b in c.student_group.batches
                             if b.name.upper() == segment),
                            None
                        )
                        if matched:
                            inferred_batch = matched
                            break

                if inferred_batch:
                    # This course targets a specific batch inferred from the course code
                    target_batches = [inferred_batch]
                else:
                    # Fallback: assign all batches in the group (e.g. a lab shared across all)
                    target_batches = list(c.student_group.batches) if c.student_group else []

            if c.course_type != CourseType.THEORY and not target_batches:
                skipped_no_batches += 1
                continue

            units_count = 1 if c.course_type == CourseType.THEORY else len(target_batches)
            session_demand[c.course_type.value] = session_demand.get(c.course_type.value, 0) + (c.weekly_sessions or 0) * units_count

            if c.course_type == CourseType.THEORY:
                required_size = c.student_group.size if c.student_group else 0
                valid_rooms = [r for r in lecture_rooms if (r.capacity or 0) >= (required_size or 0)]
            elif c.course_type == CourseType.LAB:
                max_batch_size = max((b.size or 0) for b in target_batches) if target_batches else 0
                valid_rooms = [r for r in lab_rooms if (r.capacity or 0) >= max_batch_size]
            else:
                max_batch_size = max((b.size or 0) for b in target_batches) if target_batches else 0
                valid_rooms = [r for r in tutorial_rooms if (r.capacity or 0) >= max_batch_size]

            if not valid_rooms:
                no_room_courses.append(f"{c.code} ({c.course_type.value})")

            allocations.append({
                "course": c,
                "group_id": c.student_group_id,
                "batches": target_batches, 
                "teacher_id": c.teacher_id,
                "sessions": c.weekly_sessions
            })

        if skipped_no_group:
            log(f"Skipped {skipped_no_group} courses without a division.")
        if skipped_no_teacher:
            log(f"Skipped {skipped_no_teacher} courses without an assigned teacher.")
        if skipped_no_batches:
            log(f"Skipped {skipped_no_batches} lab/tutorial courses without batches.")
        if no_room_courses:
            preview = ", ".join(no_room_courses[:10])
            suffix = "..." if len(no_room_courses) > 10 else ""
            log(f"Warning: {len(no_room_courses)} courses have no compatible room: {preview}{suffix}")
        log(f"Session demand: theory={session_demand.get('THEORY', 0)}, lab={session_demand.get('LAB', 0)}, tutorial={session_demand.get('TUTORIAL', 0)}.")
        log(f"Created {len(allocations)} course allocations.")

        # 4. Instantiate Solver
        if not allocations:
            log("Aborted: No allocations found.")
            return {"status": "SKIPPED", "reason": "No valid courses found", "logs": logs}

        if config_dict:
            config = SolverConfig(**config_dict)
        else:
            config = SolverConfig(max_time_seconds=30)
        def solve_with_config(active_config: SolverConfig, label: str):
            log(f"{label} solver time limit: {active_config.max_time_seconds} seconds.")
            log(f"{label} max total gap per division/day: {active_config.max_group_gap_hours} hour(s).")
            solver = TimetableSolver(wrapper, active_config)

            log(f"Building constraints ({label})...")
            solver.create_variables(allocations)
            solver.add_hard_constraints()
            solver.add_soft_constraints()

            log(f"Invoking OR-Tools CP-SAT solver ({label})...")
            result = solver.solve()
            log(f"{label} solving finished with status: {result.status}")
            return result

        output = solve_with_config(config, "Quality")

        if output.status == "UNKNOWN" and not output.entries and config.minimize_gaps:
            log("Quality solve timed out before finding a timetable. Retrying once with soft optimization disabled, keeping the 2-hour division gap limit.")
            relaxed_config = config.copy(update={
                "max_time_seconds": max(30, min(config.max_time_seconds, 45)),
                "enable_soft_constraints": False,
                "minimize_gaps": False,
                "max_group_gap_hours": config.max_group_gap_hours,
            })
            output = solve_with_config(relaxed_config, "Fallback")

        if output.status in ["OPTIMAL", "FEASIBLE"]:
            log(f"Saving {len(output.entries)} entries to database...")
            # 1. Clear existing for this term
            db.query(TimetableEntry).filter(TimetableEntry.term == term).delete()
            
            # 2. Add new
            for e in output.entries:
                db_entry = TimetableEntry(
                    term=term,
                    course_id=e.course_id,
                    batch_id=e.batch_id,
                    teacher_id=e.teacher_id,
                    room_id=e.room_id,
                    time_slot_id=e.time_slot_id,
                    day=e.day,
                    time_range=e.time_range,
                    student_group=e.student_group,
                    course_code=e.course_code,
                    room_name=e.room
                )
                db.add(db_entry)
            
            db.commit()
            log("Database commit successful.")
        elif output.status == "UNKNOWN":
            log("No timetable was saved because the solver reached the time limit before finding a feasible schedule.")
        elif output.status == "INFEASIBLE":
            log("No timetable was saved because the constraints are infeasible for the current data.")
        else:
            log("No timetable was saved because the solver did not return a feasible solution.")

        # Use model_dump for reliable serialization in Pydantic v2
        serialized_entries = []
        for e in output.entries:
            try:
                serialized_entries.append(e.model_dump(mode='json'))
            except AttributeError:
                serialized_entries.append(e.dict())

        return {
            "status": output.status, 
            "score": output.score,
            "entries_count": len(output.entries),
            "entries": serialized_entries,
            "logs": logs,
            "diagnostics": {
                "total_courses": len(courses),
                "allocations": len(allocations),
                "skipped_no_group": skipped_no_group,
                "skipped_no_teacher": skipped_no_teacher,
                "skipped_no_batches": skipped_no_batches,
                "courses_without_compatible_room": len(no_room_courses),
                "session_demand": session_demand,
                "rooms": {
                    "lecture": len(lecture_rooms),
                    "lab": len(lab_rooms),
                    "tutorial": len(tutorial_rooms),
                },
                "time_slots": len(slots),
            },
        }
    except Exception as exc:
        log(f"Solver failed: {exc}")
        raise
    finally:
        db.close()

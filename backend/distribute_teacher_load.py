import sys
import os
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

from app.db.session import SessionLocal
from app.models import Teacher, Course, CourseType

def distribute_load():
    db = SessionLocal()
    try:
        teachers = db.query(Teacher).all()
        courses = db.query(Course).all()
        
        # Get/Create Backup Teachers
        backup_teachers = [t for t in teachers if t.name.startswith("Auto-Teacher")]
        if not backup_teachers:
            print("No Auto-Teachers found. Cannot redistribute.")
            return
        
        # Simple iterator for backup teachers
        backup_idx = 0
        
        # Calculate Load
        t_load = {t.id: 0 for t in teachers}
        t_courses = {t.id: [] for t in teachers}
        
        for c in courses:
            if not c.teacher_id: continue
            
            sessions = c.weekly_sessions or 4
            units = 1
            if c.course_type != CourseType.THEORY:
                 if not c.batch_id and c.student_group:
                     units = len(c.student_group.batches) or 1
            
            load = sessions * units
            t_load[c.teacher_id] += load
            t_courses[c.teacher_id].append((c, load))
            
        # Check Overload (Threshold 35 to be safe)
        MAX_LOAD = 35 
        
        changes = 0
        for t in teachers:
            current_load = t_load[t.id]
            if current_load > MAX_LOAD:
                print(f"Teacher {t.name} Overloaded ({current_load} hrs). offloading...")
                
                # Sort courses by load desc (move biggest chunks first?) Or smallest?
                # Move until safe.
                # Sort descending to move big blocks quickly.
                targets = sorted(t_courses[t.id], key=lambda x: x[1], reverse=True)
                
                for course, load in targets:
                    if current_load <= MAX_LOAD:
                        break
                        
                    # Move course
                    target_t = backup_teachers[backup_idx % len(backup_teachers)]
                    # Ensure target isn't same (unlikely) and isn't overloaded?
                    # For simplicity, just round robin. Auto-teachers are empty or have huge capacity.
                    
                    print(f"  -> Moving {course.code} ({load} hrs) to {target_t.name}")
                    course.teacher_id = target_t.id
                    
                    current_load -= load
                    backup_idx += 1
                    changes += 1
        
        if changes > 0:
            db.commit()
            print(f"Successfully moved {changes} courses to resolve overload.")
        else:
            print("No overloads found (or resolved).")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    distribute_load()

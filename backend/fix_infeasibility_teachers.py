import sys
import os
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

from app.db.session import SessionLocal
from app.models.master_data import Teacher

def fix_teachers():
    db = SessionLocal()
    try:
        teachers = db.query(Teacher).all()
        
        # 1. Boost Capacity of Existing Teachers
        print("Boosting capacity of existing teachers to 40 hours/week...")
        for t in teachers:
            t.max_weekly_hours = 40
        db.commit()

        t_count = len(teachers)
        print(f"Current Teachers: {t_count}")
        
        # 2. Add New Teachers if needed (Target 8)
        needed = 8 - t_count
        if needed > 0:
            print(f"Adding {needed} Teachers to satisfy load...")
            new_teachers = []
            for i in range(needed):
                t = Teacher(
                    name=f"Auto-Teacher-{t_count + i + 1}",
                    email=f"auto.teacher.{t_count + i + 1}@example.com",
                    max_weekly_hours=40
                )
                new_teachers.append(t)
            
            db.add_all(new_teachers)
            db.commit()
            print(f"Added {len(new_teachers)} teachers.")
        else:
            print("Teacher count sufficient (>= 8).")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_teachers()

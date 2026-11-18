
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import text
from app.db.session import SessionLocal

def check_data():
    db = SessionLocal()
    try:
        # Check counts
        print("Checking Table Counts:")
        counts = {
            "teachers": db.execute(text("SELECT COUNT(*) FROM teachers")).scalar(),
            "rooms": db.execute(text("SELECT COUNT(*) FROM rooms")).scalar(),
            "student_groups": db.execute(text("SELECT COUNT(*) FROM student_groups")).scalar(),
            "batches": db.execute(text("SELECT COUNT(*) FROM batches")).scalar(),
            "courses": db.execute(text("SELECT COUNT(*) FROM courses")).scalar(),
        }
        for table, count in counts.items():
            print(f"  - {table}: {count}")
            
        print("\nSample Student Groups & Batches:")
        groups = db.execute(text("SELECT id, name FROM student_groups LIMIT 3")).fetchall()
        for g in groups:
            print(f"  Group: {g.name} (ID: {g.id})")
            batches = db.execute(text(f"SELECT name FROM batches WHERE student_group_id = '{g.id}'")).fetchall()
            b_names = [b.name for b in batches]
            print(f"    -> Batches: {b_names}")

    finally:
        db.close()

if __name__ == "__main__":
    check_data()

from app.db.session import SessionLocal
from app.models.student import StudentGroup, Batch
import uuid

def test_insert():
    db = SessionLocal()
    try:
        group = StudentGroup(
            name=f"TestGroup-{uuid.uuid4().hex[:4]}",
            size=60,
            year_level=1
        )
        db.add(group)
        db.flush()
        print(f"Group created with ID: {group.id}")
        
        batch = Batch(
            name="T1",
            size=20,
            student_group_id=group.id
        )
        db.add(batch)
        db.commit()
        print("Commit successful.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_insert()

from app.db.session import SessionLocal
from app.models import TimetableEntry, Course

db = SessionLocal()
entries = db.query(TimetableEntry).join(Course).filter(Course.course_type == 'THEORY').all()
print(f"Total Theory entries: {len(entries)}")
for e in entries:
    print(f"Entry: {e.course_code} | Group: {e.student_group} | Batch: {e.batch_id} | Day: {e.day} | Time: {e.time_range}")
db.close()

from app.db.session import SessionLocal
from app.models import Course, StudentGroup, Batch

db = SessionLocal()
courses = db.query(Course).all()
print(f"Total courses: {len(courses)}")
for c in courses:
    group_name = c.student_group.name if c.student_group else "None"
    batch_name = c.batch.name if c.batch else "None"
    print(f"Course: {c.code} - {c.name} | Type: {c.course_type} | Group: {group_name} | Batch: {batch_name}")
db.close()

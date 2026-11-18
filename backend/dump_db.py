from app.db.session import SessionLocal
from app.models import Course, TimetableEntry
import json

db = SessionLocal()
courses = db.query(Course).all()

course_list = []
for c in courses:
    course_list.append({
        "id": str(c.id),
        "code": c.code,
        "name": c.name,
        "type": c.course_type.value if c.course_type else None,
        "batch_id": str(c.batch_id) if c.batch_id else None
    })

entries = db.query(TimetableEntry).all()
entry_list = []
for e in entries:
    entry_list.append({
        "course_code": e.course_code,
        "batch_id": str(e.batch_id) if e.batch_id else None,
        "room_name": e.room_name,
        "day": e.day,
        "time_range": e.time_range
    })

with open("dump.json", "w") as f:
    json.dump({"courses": course_list, "entries": entry_list}, f, indent=2)

db.close()
print("Dumped to dump.json")

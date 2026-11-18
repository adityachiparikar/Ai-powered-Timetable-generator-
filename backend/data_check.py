from app.db.session import SessionLocal
from app.models import Course, Teacher, StudentGroup

def diagnostic():
    db = SessionLocal()
    courses = db.query(Course).all()
    print(f"Total Courses: {len(courses)}")
    
    missing_teacher = 0
    missing_group = 0
    for c in courses:
        if not c.teacher_id:
            missing_teacher += 1
            print(f"ERR: Course {c.code} has no teacher!")
        if not c.student_group_id:
            missing_group += 1
            print(f"ERR: Course {c.code} has no student group!")
            
    print(f"Summary: {missing_teacher} missing teacher, {missing_group} missing group.")
    db.close()

if __name__ == "__main__":
    diagnostic()

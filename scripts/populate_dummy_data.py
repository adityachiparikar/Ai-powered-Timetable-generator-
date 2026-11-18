"""
Populate database with dummy data for Computer Science department
- 6 SY (Second Year) divisions
- 6 TY (Third Year) divisions
- Teachers, Courses, Rooms, and Time Slots
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.master_data import Teacher, Room, TimeSlot
from app.models.student import StudentGroup, Batch
from app.models.course import Course, CourseType
from datetime import time

def clear_existing_data(db: Session):
    """Clear existing data to start fresh"""
    print("🗑️  Clearing existing data...")
    db.query(Course).delete()
    db.query(Batch).delete()
    db.query(StudentGroup).delete()
    db.query(TimeSlot).delete()
    db.query(Room).delete()
    db.query(Teacher).delete()
    db.commit()
    print("✅ Existing data cleared")

def create_teachers(db: Session):
    """Create teachers for various subjects"""
    print("\n👨‍🏫 Creating teachers...")
    
    teachers_data = [
        # Theory Teachers
        {"name": "Dr. Amit Sharma", "email": "amit.sharma@university.edu", "max_weekly_hours": 20},
        {"name": "Prof. Priya Patel", "email": "priya.patel@university.edu", "max_weekly_hours": 18},
        {"name": "Dr. Rajesh Kumar", "email": "rajesh.kumar@university.edu", "max_weekly_hours": 20},
        {"name": "Prof. Sneha Desai", "email": "sneha.desai@university.edu", "max_weekly_hours": 18},
        {"name": "Dr. Vikram Singh", "email": "vikram.singh@university.edu", "max_weekly_hours": 20},
        {"name": "Prof. Anjali Mehta", "email": "anjali.mehta@university.edu", "max_weekly_hours": 18},
        {"name": "Dr. Suresh Reddy", "email": "suresh.reddy@university.edu", "max_weekly_hours": 20},
        {"name": "Prof. Kavita Joshi", "email": "kavita.joshi@university.edu", "max_weekly_hours": 18},
        {"name": "Dr. Arun Verma", "email": "arun.verma@university.edu", "max_weekly_hours": 20},
        {"name": "Prof. Deepa Nair", "email": "deepa.nair@university.edu", "max_weekly_hours": 18},
        
        # Lab Teachers
        {"name": "Mr. Rahul Gupta", "email": "rahul.gupta@university.edu", "max_weekly_hours": 24},
        {"name": "Ms. Pooja Shah", "email": "pooja.shah@university.edu", "max_weekly_hours": 24},
        {"name": "Mr. Karan Malhotra", "email": "karan.malhotra@university.edu", "max_weekly_hours": 24},
        {"name": "Ms. Neha Kapoor", "email": "neha.kapoor@university.edu", "max_weekly_hours": 24},
        {"name": "Mr. Sanjay Rao", "email": "sanjay.rao@university.edu", "max_weekly_hours": 24},
    ]
    
    teachers = []
    for data in teachers_data:
        teacher = Teacher(**data)
        db.add(teacher)
        teachers.append(teacher)
    
    db.commit()
    print(f"✅ Created {len(teachers)} teachers")
    return teachers

def create_rooms(db: Session):
    """Create classrooms and labs"""
    print("\n🏫 Creating rooms...")
    
    rooms_data = [
        # Theory Classrooms
        {"name": "Room 101", "capacity": 60, "is_lab": False, "building": "Main Block"},
        {"name": "Room 102", "capacity": 60, "is_lab": False, "building": "Main Block"},
        {"name": "Room 103", "capacity": 60, "is_lab": False, "building": "Main Block"},
        {"name": "Room 104", "capacity": 60, "is_lab": False, "building": "Main Block"},
        {"name": "Room 201", "capacity": 60, "is_lab": False, "building": "Main Block"},
        {"name": "Room 202", "capacity": 60, "is_lab": False, "building": "Main Block"},
        {"name": "Room 203", "capacity": 60, "is_lab": False, "building": "Main Block"},
        {"name": "Room 204", "capacity": 60, "is_lab": False, "building": "Main Block"},
        {"name": "Room 301", "capacity": 60, "is_lab": False, "building": "Main Block"},
        {"name": "Room 302", "capacity": 60, "is_lab": False, "building": "Main Block"},
        
        # Computer Labs
        {"name": "CS Lab 1", "capacity": 30, "is_lab": True, "building": "CS Block"},
        {"name": "CS Lab 2", "capacity": 30, "is_lab": True, "building": "CS Block"},
        {"name": "CS Lab 3", "capacity": 30, "is_lab": True, "building": "CS Block"},
        {"name": "CS Lab 4", "capacity": 30, "is_lab": True, "building": "CS Block"},
        {"name": "CS Lab 5", "capacity": 30, "is_lab": True, "building": "CS Block"},
        {"name": "CS Lab 6", "capacity": 30, "is_lab": True, "building": "CS Block"},
    ]
    
    rooms = []
    for data in rooms_data:
        room = Room(**data)
        db.add(room)
        rooms.append(room)
    
    db.commit()
    print(f"✅ Created {len(rooms)} rooms")
    return rooms

def create_time_slots(db: Session):
    """Create time slots for the week"""
    print("\n⏰ Creating time slots...")
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    slots = [
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 15), time(12, 15)),  # After break
        (time(12, 15), time(13, 15)),
        (time(14, 0), time(15, 0)),    # After lunch
        (time(15, 0), time(16, 0)),
    ]
    
    time_slots = []
    for day in days:
        for start, end in slots:
            slot = TimeSlot(
                day_of_week=day,
                start_time=start,
                end_time=end,
                is_break=False
            )
            db.add(slot)
            time_slots.append(slot)
    
    db.commit()
    print(f"✅ Created {len(time_slots)} time slots")
    return time_slots

def create_student_groups(db: Session):
    """Create student groups (divisions) for SY and TY"""
    print("\n👥 Creating student groups...")
    
    groups = []
    
    # Second Year (SY) - 6 divisions
    for i in range(1, 7):
        group = StudentGroup(
            name=f"CS-SY-Div{chr(64+i)}",  # CS-SY-DivA, CS-SY-DivB, etc.
            size=60,
            year_level=2
        )
        db.add(group)
        db.flush()  # Get the ID
        
        # Create 3 batches per division for labs
        # Create 3 batches per division for labs
        batch_names = ["b1", "b2", "b3"]
        for batch_name in batch_names:
            batch = Batch(
                name=batch_name, 
                size=20, # Reduced size since 3 batches * 20 = 60 students
                student_group_id=group.id
            )
            db.add(batch)
        
        groups.append(group)
    
    # Third Year (TY) - 6 divisions
    for i in range(1, 7):
        group = StudentGroup(
            name=f"CS-TY-Div{chr(64+i)}",  # CS-TY-DivA, CS-TY-DivB, etc.
            size=60,
            year_level=3
        )
        db.add(group)
        db.flush()  # Get the ID
        
        # Create 3 batches per division for labs
        # Create 3 batches per division for labs
        batch_names = ["b1", "b2", "b3"]
        for batch_name in batch_names:
            batch = Batch(
                name=batch_name,
                size=20,
                student_group_id=group.id
            )
            db.add(batch)
        
        groups.append(group)
    
    db.commit()
    print(f"✅ Created {len(groups)} student groups (12 divisions with 24 batches)")
    return groups

def create_courses(db: Session, teachers, groups):
    """Create courses for SY and TY"""
    print("\n📚 Creating courses...")
    
    # Get SY and TY groups
    sy_groups = [g for g in groups if g.year_level == 2]
    ty_groups = [g for g in groups if g.year_level == 3]
    
    courses = []
    
    # SY Theory Courses (5 subjects per division)
    sy_subjects = [
        ("Data Structures", "DS", 4),
        ("Object Oriented Programming", "OOP", 4),
        ("Computer Organization", "CO", 3),
        ("Discrete Mathematics", "DM", 3),
        ("Database Management Systems", "DBMS", 4),
    ]
    
    teacher_idx = 0
    for group in sy_groups:
        for subject_name, code, sessions in sy_subjects:
            course = Course(
                code=f"{code}-{group.name}",
                name=subject_name,
                course_type=CourseType.THEORY,
                weekly_sessions=sessions,
                teacher_id=teachers[teacher_idx % 10].id,  # Rotate through theory teachers
                student_group_id=group.id
            )
            db.add(course)
            courses.append(course)
            teacher_idx += 1
    
    # SY Lab Courses (2 labs per division)
    sy_labs = [
        ("Data Structures Lab", "DSL", 2),
        ("OOP Lab", "OOPL", 2),
    ]
    
    for group in sy_groups:
        # Get batches for this group
        batches = db.query(Batch).filter(Batch.student_group_id == group.id).all()
        
        for lab_name, code, sessions in sy_labs:
            for batch in batches:
                course = Course(
                    code=f"{code}-{group.name}-{batch.name}",
                    name=lab_name,
                    course_type=CourseType.LAB,
                    weekly_sessions=sessions,
                    teacher_id=teachers[10 + (teacher_idx % 5)].id,  # Use lab teachers
                    student_group_id=group.id,
                    batch_id=batch.id
                )
                db.add(course)
                courses.append(course)
                teacher_idx += 1
    
    # TY Theory Courses (5 subjects per division)
    ty_subjects = [
        ("Software Engineering", "SE", 4),
        ("Computer Networks", "CN", 4),
        ("Operating Systems", "OS", 3),
        ("Theory of Computation", "TOC", 3),
        ("Web Technologies", "WT", 4),
    ]
    
    for group in ty_groups:
        for subject_name, code, sessions in ty_subjects:
            course = Course(
                code=f"{code}-{group.name}",
                name=subject_name,
                course_type=CourseType.THEORY,
                weekly_sessions=sessions,
                teacher_id=teachers[teacher_idx % 10].id,
                student_group_id=group.id
            )
            db.add(course)
            courses.append(course)
            teacher_idx += 1
    
    # TY Lab Courses (2 labs per division)
    ty_labs = [
        ("Software Engineering Lab", "SEL", 2),
        ("Web Technologies Lab", "WTL", 2),
    ]
    
    for group in ty_groups:
        # Get batches for this group
        batches = db.query(Batch).filter(Batch.student_group_id == group.id).all()
        
        for lab_name, code, sessions in ty_labs:
            for batch in batches:
                course = Course(
                    code=f"{code}-{group.name}-{batch.name}",
                    name=lab_name,
                    course_type=CourseType.LAB,
                    weekly_sessions=sessions,
                    teacher_id=teachers[10 + (teacher_idx % 5)].id,
                    student_group_id=group.id,
                    batch_id=batch.id
                )
                db.add(course)
                courses.append(course)
                teacher_idx += 1
    
    db.commit()
    print(f"✅ Created {len(courses)} courses")
    return courses

def main():
    """Main function to populate all dummy data"""
    print("=" * 60)
    print("🚀 Populating Database with Dummy Data")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_existing_data(db)
        
        # Create all entities
        teachers = create_teachers(db)
        rooms = create_rooms(db)
        time_slots = create_time_slots(db)
        groups = create_student_groups(db)
        courses = create_courses(db, teachers, groups)
        
        print("\n" + "=" * 60)
        print("✅ DATABASE POPULATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   - Teachers: {len(teachers)}")
        print(f"   - Rooms: {len(rooms)}")
        print(f"   - Time Slots: {len(time_slots)}")
        print(f"   - Student Groups: {len(groups)} (6 SY + 6 TY divisions)")
        print(f"   - Batches: 36 (3 per division)")
        print(f"   - Courses: {len(courses)}")
        print(f"\n🎯 Ready to generate timetable!")
        print(f"   Visit http://localhost:5173 to generate the timetable\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()

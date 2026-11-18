"""
Seed script to populate the database with dummy data for CS Department
- SY (Second Year): 6 Divisions (A-F)
- TY (Third Year): 6 Divisions (A-F)
- Each division has 3 batches
- Mix of Theory and Lab courses
"""

import sys
import os
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models import Teacher, Room, StudentGroup, Batch, Course, TimeSlot, CourseType
from datetime import time

db = SessionLocal()

try:
    # Clear existing data
    print("Clearing existing data...")
    db.query(Course).delete()
    db.query(Batch).delete()
    db.query(StudentGroup).delete()
    db.query(TimeSlot).delete()
    db.query(Room).delete()
    db.query(Teacher).delete()
    db.commit()

    # 1. Create Teachers (15 faculty members)
    print("Creating teachers...")
    teachers = [
        Teacher(name="Dr. Sharma", email="sharma@cs.edu", max_weekly_hours=20),
        Teacher(name="Prof. Patel", email="patel@cs.edu", max_weekly_hours=20),
        Teacher(name="Dr. Kumar", email="kumar@cs.edu", max_weekly_hours=20),
        Teacher(name="Prof. Singh", email="singh@cs.edu", max_weekly_hours=20),
        Teacher(name="Dr. Reddy", email="reddy@cs.edu", max_weekly_hours=20),
        Teacher(name="Prof. Mehta", email="mehta@cs.edu", max_weekly_hours=20),
        Teacher(name="Dr. Gupta", email="gupta@cs.edu", max_weekly_hours=20),
        Teacher(name="Prof. Verma", email="verma@cs.edu", max_weekly_hours=20),
        Teacher(name="Dr. Joshi", email="joshi@cs.edu", max_weekly_hours=20),
        Teacher(name="Prof. Desai", email="desai@cs.edu", max_weekly_hours=20),
        Teacher(name="Dr. Nair", email="nair@cs.edu", max_weekly_hours=20),
        Teacher(name="Prof. Iyer", email="iyer@cs.edu", max_weekly_hours=20),
        Teacher(name="Dr. Rao", email="rao@cs.edu", max_weekly_hours=20),
        Teacher(name="Prof. Kulkarni", email="kulkarni@cs.edu", max_weekly_hours=20),
        Teacher(name="Dr. Menon", email="menon@cs.edu", max_weekly_hours=20),
    ]
    for t in teachers:
        db.add(t)
    db.commit()
    print(f"Created {len(teachers)} teachers")

    # 2. Create Rooms (20 rooms: 12 classrooms + 8 labs)
    print("Creating rooms...")
    rooms = []
    # Classrooms
    for i in range(1, 13):
        rooms.append(Room(name=f"Room {i}", capacity=60, is_lab=False, building="Main Block"))
    # Labs
    for i in range(1, 9):
        rooms.append(Room(name=f"Lab {i}", capacity=30, is_lab=True, building="Lab Block"))
    
    for r in rooms:
        db.add(r)
    db.commit()
    print(f"Created {len(rooms)} rooms")

    # 3. Create Time Slots (Monday-Friday, 9 AM - 5 PM, 1-hour slots)
    print("Creating time slots...")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    time_slots = []
    
    for day in days:
        # Morning slots: 9-12
        for hour in [9, 10, 11]:
            time_slots.append(TimeSlot(
                day_of_week=day,
                start_time=time(hour, 0),
                end_time=time(hour + 1, 0),
                is_break=False
            ))
        
        # Lunch break
        time_slots.append(TimeSlot(
            day_of_week=day,
            start_time=time(12, 0),
            end_time=time(13, 0),
            is_break=True
        ))
        
        # Afternoon slots: 13-17
        for hour in [13, 14, 15, 16]:
            time_slots.append(TimeSlot(
                day_of_week=day,
                start_time=time(hour, 0),
                end_time=time(hour + 1, 0),
                is_break=False
            ))
    
    for ts in time_slots:
        db.add(ts)
    db.commit()
    print(f"Created {len(time_slots)} time slots")

    # 4. Create Student Groups (12 divisions: SY A-F, TY A-F)
    print("Creating student groups and batches...")
    student_groups = []
    
    for year, year_name in [(2, "SY"), (3, "TY")]:
        for div in ["A", "B", "C", "D", "E", "F"]:
            group = StudentGroup(
                name=f"CS-{year_name}-{div}",
                size=60,
                year_level=year
            )
            db.add(group)
            db.flush()  # Get the ID
            
            # Create 3 batches per division
            for batch_name in ["A", "B", "C"]:
                batch = Batch(
                    name=f"Batch {batch_name}",
                    size=20,
                    student_group_id=group.id
                )
                db.add(batch)
            
            student_groups.append(group)
    
    db.commit()
    print(f"Created {len(student_groups)} student groups with 3 batches each")

    # 5. Create Courses
    print("Creating courses...")
    
    # Refresh student groups to get batches
    db.expire_all()
    student_groups = db.query(StudentGroup).all()
    teachers_list = db.query(Teacher).all()
    
    course_templates = {
        "SY": [
            {"code": "CS201", "name": "Data Structures", "type": CourseType.THEORY, "sessions": 4},
            {"code": "CS202", "name": "Database Management", "type": CourseType.THEORY, "sessions": 4},
            {"code": "CS203", "name": "Operating Systems", "type": CourseType.THEORY, "sessions": 3},
            {"code": "CS204", "name": "Computer Networks", "type": CourseType.THEORY, "sessions": 3},
            {"code": "CS205L", "name": "DS Lab", "type": CourseType.LAB, "sessions": 2},
            {"code": "CS206L", "name": "DBMS Lab", "type": CourseType.LAB, "sessions": 2},
        ],
        "TY": [
            {"code": "CS301", "name": "Software Engineering", "type": CourseType.THEORY, "sessions": 4},
            {"code": "CS302", "name": "Web Technologies", "type": CourseType.THEORY, "sessions": 4},
            {"code": "CS303", "name": "Machine Learning", "type": CourseType.THEORY, "sessions": 3},
            {"code": "CS304", "name": "Cloud Computing", "type": CourseType.THEORY, "sessions": 3},
            {"code": "CS305L", "name": "Web Tech Lab", "type": CourseType.LAB, "sessions": 2},
            {"code": "CS306L", "name": "ML Lab", "type": CourseType.LAB, "sessions": 2},
        ]
    }
    
    courses_created = 0
    teacher_idx = 0
    
    for group in student_groups:
        year_key = "SY" if group.year_level == 2 else "TY"
        templates = course_templates[year_key]
        
        for template in templates:
            # For theory courses, create one course per division
            if template["type"] == CourseType.THEORY:
                course = Course(
                    code=f"{template['code']}-{group.name}",
                    name=template["name"],
                    course_type=template["type"],
                    weekly_sessions=template["sessions"],
                    teacher_id=teachers_list[teacher_idx % len(teachers_list)].id,
                    student_group_id=group.id,
                    batch_id=None  # Theory is for whole class
                )
                db.add(course)
                courses_created += 1
                teacher_idx += 1
            
            # For lab courses, create one course per batch
            else:
                for batch in group.batches:
                    course = Course(
                        code=f"{template['code']}-{group.name}-{batch.name}",
                        name=template["name"],
                        course_type=template["type"],
                        weekly_sessions=template["sessions"],
                        teacher_id=teachers_list[teacher_idx % len(teachers_list)].id,
                        student_group_id=group.id,
                        batch_id=batch.id  # Lab is for specific batch
                    )
                    db.add(course)
                    courses_created += 1
                teacher_idx += 1
    
    db.commit()
    print(f"Created {courses_created} courses")

    print("\n=== Database seeded successfully! ===")
    print(f"Total Teachers: {db.query(Teacher).count()}")
    print(f"Total Rooms: {db.query(Room).count()}")
    print(f"Total Student Groups: {db.query(StudentGroup).count()}")
    print(f"Total Batches: {db.query(Batch).count()}")
    print(f"Total Courses: {db.query(Course).count()}")
    print(f"Total Time Slots: {db.query(TimeSlot).count()}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

import sys
import os
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

from app.db.session import SessionLocal
from app.models import Room, Course, TimeSlot

def check_types():
    db = SessionLocal()
    try:
        room = db.query(Room).first()
        course = db.query(Course).first()
        slot = db.query(TimeSlot).first()
        
        print(f"Room ID: {room.id} (Type: {type(room.id)})")
        print(f"Course ID: {course.id} (Type: {type(course.id)})")
        if slot:
            print(f"Slot ID: {slot.id} (Type: {type(slot.id)})")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_types()

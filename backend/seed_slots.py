import sys
import os
from datetime import time
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

from app.db.session import SessionLocal
from app.models.master_data import TimeSlot

def seed_slots():
    db = SessionLocal()
    try:
        if db.query(TimeSlot).count() > 0:
            print("Time slots already exist. Skipping seed.")
            return

        print("Seeding default time slots (Mon-Fri, 09:00 - 17:00)...")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        
        slots = []
        for day in days:
            for hour in range(9, 17): # 9 to 16 start times (ending 10 to 17)
                is_break = (hour == 13) # 1 PM Lunch Break
                slot = TimeSlot(
                    day_of_week=day,
                    start_time=time(hour, 0),
                    end_time=time(hour + 1, 0),
                    is_break=is_break
                )
                slots.append(slot)
        
        db.add_all(slots)
        db.commit()
        print(f"Successfully added {len(slots)} time slots.")
        
    except Exception as e:
        print(f"Error seeding slots: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_slots()

import sys
import os
from datetime import time
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

from app.db.session import SessionLocal
from app.models.master_data import TimeSlot

def update_slots():
    db = SessionLocal()
    try:
        # 1. Clear existing slots
        print("Deleting existing Time Slots...")
        db.query(TimeSlot).delete()
        db.commit()
        
        # 2. Add new 8 AM - 6 PM slots for MON-SAT
        print("Seeding Time Slots (Mon-Sat, 08:00 - 18:00)...")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        
        start_h = 8
        end_h = 18 
        
        new_slots = []
        for day in days:
            for hour in range(start_h, end_h):
                is_break = (hour == 13) # 1 PM - 2 PM Break
                
                slot = TimeSlot(
                    day_of_week=day,
                    start_time=time(hour, 0),
                    end_time=time(hour + 1, 0),
                    is_break=is_break
                )
                new_slots.append(slot)
        
        db.add_all(new_slots)
        db.commit()
        print(f"Successfully seeded {len(new_slots)} slots (10 per day * 6 days = 60).")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_slots()

import sys
import os
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

from app.db.session import SessionLocal
from app.models.master_data import Room

def fix_resources():
    db = SessionLocal()
    try:
        rooms = db.query(Room).all()
        lab_count = sum(1 for r in rooms if r.is_lab)
        tut_count = sum(1 for r in rooms if getattr(r, 'is_tutorial_room', False))
        
        print(f"Current Labs: {lab_count}")
        print(f"Current Tutorial Rooms: {tut_count}")
        
        new_rooms = []
        
        # We need roughly 6 Labs for 36 Lab courses
        needed_labs = 6 - lab_count
        if needed_labs > 0:
            print(f"Adding {needed_labs} Laboratory Rooms to satisfy capacity...")
            for i in range(needed_labs):
                r = Room(
                    name=f"Auto-Lab-{lab_count + i + 1}",
                    capacity=40,
                    is_lab=True,
                    is_tutorial_room=False,
                    building="Main Block"
                )
                new_rooms.append(r)

        # We need at least 1 Tutorial Room if we want to run tutorials (even if 0 courses now, user might add)
        # But wait, debug showed 0 Tutorial Courses. So strict necessity is 0.
        # But providing 1 is helpful.
        if tut_count == 0:
             print("Adding 1 Default Tutorial Room...")
             r = Room(
                name="Tutorial-Room-1",
                capacity=30,
                is_lab=False,
                is_tutorial_room=True,
                building="Annex"
             )
             new_rooms.append(r)
        
        if new_rooms:
            db.add_all(new_rooms)
            db.commit()
            print(f"Successfully added {len(new_rooms)} rooms.")
        else:
            print("No extra rooms needed based on heuristic.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_resources()

from sqlalchemy import Column, String, ForeignKey, UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import uuid

class TimetableEntry(Base):
    __tablename__ = "timetable_entries"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    term = Column(String, index=True) # e.g. "Spring 2024"
    
    course_id = Column(ForeignKey("courses.id"), nullable=False)
    batch_id = Column(ForeignKey("batches.id"), nullable=True)
    teacher_id = Column(ForeignKey("teachers.id"), nullable=True)
    room_id = Column(ForeignKey("rooms.id"), nullable=False)
    time_slot_id = Column(ForeignKey("timeslots.id"), nullable=False)
    
    # Redundant but helpful for fast queries
    day = Column(String)
    time_range = Column(String)
    student_group = Column(String)
    course_code = Column(String)
    room_name = Column(String)

    # Relationships
    course = relationship("Course")
    batch = relationship("Batch")
    teacher = relationship("Teacher")
    room = relationship("Room")
    time_slot = relationship("TimeSlot")

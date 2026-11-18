from sqlalchemy import Column, String, Integer, Boolean, Time, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Teacher(Base):
    __table_args__ = {"extend_existing": True}
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    max_weekly_hours = Column(Integer, default=20)
    
    # Relationships
    courses = relationship("Course", back_populates="teacher")
    # Add constraint relationships later

class Room(Base):
    __table_args__ = {"extend_existing": True}
    name = Column(String, unique=True, index=True)
    capacity = Column(Integer)
    is_lab = Column(Boolean, default=False)
    is_tutorial_room = Column(Boolean, default=False)
    building = Column(String)

class TimeSlot(Base):
    __table_args__ = {"extend_existing": True}
    day_of_week = Column(String, index=True) # Monday, Tuesday...
    start_time = Column(Time)
    end_time = Column(Time)
    is_break = Column(Boolean, default=False)

class GlobalBreak(Base):
    __table_args__ = {"extend_existing": True}
    name = Column(String, index=True)
    start_time = Column(Time)
    end_time = Column(Time)

class TeacherConstraint(Base):
    __table_args__ = {"extend_existing": True}
    teacher_id = Column(ForeignKey("teachers.id", ondelete="CASCADE"), index=True)
    day_of_week = Column(String) # or None for all days
    start_time = Column(Time)
    end_time = Column(Time)
    is_available = Column(Boolean, default=False) # If False, teacher is BUSY during this time
    
    teacher = relationship("Teacher", backref="specific_constraints")

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum
from sqlalchemy import Enum

class CourseType(str, enum.Enum):
    THEORY = "THEORY"
    LAB = "LAB"
    TUTORIAL = "TUTORIAL"

class Course(Base):
    __table_args__ = {"extend_existing": True}
    code = Column(String, unique=True, index=True)
    name = Column(String)
    course_type = Column(Enum(CourseType), default=CourseType.THEORY)
    weekly_sessions = Column(Integer) # Per batch if LAB
    
    teacher_id = Column(ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    teacher = relationship("Teacher", back_populates="courses", lazy="selectin")
    
    student_group_id = Column(ForeignKey("student_groups.id", ondelete="SET NULL"), nullable=True)
    student_group = relationship("StudentGroup", lazy="selectin")

    batch_id = Column(ForeignKey("batches.id", ondelete="SET NULL"), nullable=True)
    batch = relationship("Batch", lazy="selectin")
    # Usually a course belongs to a curriculum. 
    # For scheduling, we define "Class Sessions".
    # But usually a Course entity links to a Teacher and a Subject.

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class StudentGroup(Base):
    __tablename__ = "student_groups"
    __table_args__ = {"extend_existing": True}
    
    name = Column(String, unique=True, index=True) # e.g. "CS-Year1-DivA"
    size = Column(Integer)
    year_level = Column(Integer)
    
    batches = relationship("Batch", back_populates="student_group", cascade="all, delete-orphan", lazy="selectin")

class Batch(Base):
    __tablename__ = "batches"
    __table_args__ = {"extend_existing": True}
    name = Column(String, index=True) # e.g. "A1"
    size = Column(Integer)
    student_group_id = Column(ForeignKey("student_groups.id"))
    
    student_group = relationship("StudentGroup", back_populates="batches")

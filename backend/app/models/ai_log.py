from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base_class import Base

class ConstraintLog(Base):
    """
    Logs every time a user manually overrides a generated timetable.
    This data is used to train the ML model to learn soft constraint weights.
    """
    __table_args__ = {"extend_existing": True}
    user_id = Column(String, index=True) # ID of user who made the change
    
    # Context
    term = Column(String)
    
    # The change event
    original_assignment = Column(JSON) # {course_id, slot_id, room_id}
    new_assignment = Column(JSON)      # {course_id, slot_id, room_id}
    
    # Reason (Optional explicit feedback)
    reason_category = Column(String, nullable=True) # e.g. "Teacher Unavailable", "Room too small"
    reason_text = Column(String, nullable=True)     # NLP Input
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class MLModelArtifact(Base):
    """
    Stores metadata about trained ML models.
    """
    __table_args__ = {"extend_existing": True}
    version = Column(String, unique=True)
    accuracy_score = Column(Float)
    features_config = Column(JSON) # Which features were used
    file_path = Column(String) # Path to .pkl or registry URI
    is_active = Column(Integer, default=0) # 1 if currently used
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

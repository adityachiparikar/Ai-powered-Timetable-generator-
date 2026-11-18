from sqlalchemy import Column, String, Boolean
from app.db.base_class import Base

class User(Base):
    __table_args__ = {"extend_existing": True}
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

from pydantic import BaseModel
from datetime import time
from typing import Optional
from uuid import UUID

class GlobalBreakBase(BaseModel):
    name: str
    start_time: time
    end_time: time

class GlobalBreakCreate(GlobalBreakBase):
    pass

class GlobalBreakUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class GlobalBreakResponse(GlobalBreakBase):
    id: UUID

    class Config:
        from_attributes = True

from pydantic import Field
from typing import Optional
from .base_schema import SchemaBase, IDSchema

class RoomBase(SchemaBase):
    name: str = Field(..., min_length=1, max_length=50)
    is_lab: bool = False
    capacity: Optional[int] = None

class RoomCreate(RoomBase):
    pass

class RoomUpdate(RoomBase):
    name: Optional[str] = None
    is_lab: Optional[bool] = None
    capacity: Optional[int] = None

class RoomResponse(RoomBase, IDSchema):
    pass

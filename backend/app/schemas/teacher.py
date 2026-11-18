from pydantic import EmailStr, Field
from typing import Optional
from .base_schema import SchemaBase, IDSchema

class TeacherBase(SchemaBase):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    max_weekly_hours: int = Field(20, ge=1, le=100)

class TeacherCreate(TeacherBase):
    pass

class TeacherUpdate(SchemaBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    max_weekly_hours: Optional[int] = None

class TeacherResponse(TeacherBase, IDSchema):
    pass

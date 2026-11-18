from pydantic import Field
from typing import Optional, List
from uuid import UUID
from .base_schema import SchemaBase, IDSchema

class BatchBase(SchemaBase):
    name: str = Field(..., min_length=1)
    size: int = Field(..., ge=1)

class BatchCreate(BatchBase):
    pass

class BatchResponse(BatchBase, IDSchema):
    student_group_id: UUID

class StudentGroupBase(SchemaBase):
    name: str = Field(..., min_length=2)
    size: int = Field(..., ge=1)
    year_level: int = Field(..., ge=1, le=5)

class StudentGroupCreate(StudentGroupBase):
    pass

class StudentGroupUpdate(SchemaBase):
    name: Optional[str] = None
    size: Optional[int] = None
    year_level: Optional[int] = None

class StudentGroupResponse(StudentGroupBase, IDSchema):
    batches: List[BatchResponse] = []

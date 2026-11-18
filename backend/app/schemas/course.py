from pydantic import Field
from typing import Optional
from uuid import UUID
from .base_schema import SchemaBase, IDSchema
from .teacher import TeacherBase
from .student import StudentGroupBase, BatchBase
from app.models.course import CourseType

class CourseBase(SchemaBase):
    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    course_type: CourseType = CourseType.THEORY
    weekly_sessions: int = Field(..., ge=1)
    teacher_id: Optional[UUID] = None
    student_group_id: UUID  # Required - courses must belong to a division
    batch_id: Optional[UUID] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(CourseBase):
    code: Optional[str] = None
    name: Optional[str] = None
    course_type: Optional[CourseType] = None
    weekly_sessions: Optional[int] = None
    teacher_id: Optional[UUID] = None
    student_group_id: Optional[UUID] = None
    batch_id: Optional[UUID] = None

class CourseResponse(CourseBase, IDSchema):
    student_group_id: Optional[UUID] = None
    teacher: Optional[TeacherBase] = None
    student_group: Optional[StudentGroupBase] = None
    batch: Optional[BatchBase] = None

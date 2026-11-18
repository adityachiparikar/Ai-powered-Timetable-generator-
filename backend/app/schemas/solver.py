from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from enum import Enum

class ConstraintType(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"

class SolverConfig(BaseModel):
    max_time_seconds: int = 90
    num_workers: int = 8
    enable_soft_constraints: bool = True
    max_daily_load: int = 4
    minimize_gaps: bool = True
    max_group_gap_hours: int = Field(default=2, ge=0, le=6)
    consecutive_labs: bool = True
    parallel_labs: bool = True

class SolutionEntry(BaseModel):
    course_id: UUID
    batch_id: Optional[UUID] = None # None if Theory (whole group)
    teacher_id: Optional[UUID] = None
    room_id: UUID
    time_slot_id: UUID
    day: str
    time_range: str
    course_code: Optional[str] = None
    student_group: Optional[str] = None
    course_type: Optional[str] = None
    room: Optional[str] = None

class SolverOutput(BaseModel):
    status: str # OPTIMAL, FEASIBLE, INFEASIBLE
    score: float
    entries: List[SolutionEntry]
    conflicts: List[str] = []
    metadata: Dict[str, Any] = {}

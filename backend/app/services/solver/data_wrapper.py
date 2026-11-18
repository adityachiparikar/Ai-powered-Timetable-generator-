from typing import List, Dict, Any
from app.models import Teacher, Course, Room, StudentGroup, Batch, TimeSlot, CourseType

class SolverDataWrapper:
    """
    Prepares SQLAlchemy objects into an index-based format for CP-SAT.
    mappings: id -> index
    reverse_mappings: index -> id
    """
    def __init__(
        self, 
        teachers: List[Teacher], 
        courses: List[Course], 
        rooms: List[Room], 
        groups: List[StudentGroup],
        slots: List[TimeSlot]
    ):
        self.teachers = teachers
        self.courses = courses
        self.rooms = rooms
        self.groups = groups
        self.slots = slots
        
        # Mappings
        self.t_map = {t.id: i for i, t in enumerate(teachers)}
        self.c_map = {c.id: i for i, c in enumerate(courses)}
        self.r_map = {r.id: i for i, r in enumerate(rooms)}
        self.s_map = {s.id: i for i, s in enumerate(slots)}
        
        # Group/Batch Mapping: Flattening hierarchy
        # We need a unified list of "StudentEntities" for conflict checking
        # But for assignment, we assign Courses. 
        # A Course is linked to a StudentGroup or a Batch?
        # In our schema, Course doesn't link to Group directly yet (my oversight in Phase 1).
        # FIX: We need input data to link Course -> Group/Batch.
        # For now, we assume the Solver Input includes this mapping.
        
    def get_teacher_idx(self, id): return self.t_map.get(id)
    def get_room_idx(self, id): return self.r_map.get(id)
    def get_slot_idx(self, id): return self.s_map.get(id)

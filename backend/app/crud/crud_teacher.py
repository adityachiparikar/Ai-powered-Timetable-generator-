from app.crud.base import CRUDBase
from app.models.master_data import Teacher
from app.schemas.teacher import TeacherCreate, TeacherUpdate

class CRUDTeacher(CRUDBase[Teacher, TeacherCreate, TeacherUpdate]):
    pass

teacher = CRUDTeacher(Teacher)

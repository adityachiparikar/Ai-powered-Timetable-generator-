from app.crud.base import CRUDBase
from app.models.master_data import GlobalBreak
from app.schemas.master_data_break import GlobalBreakCreate, GlobalBreakUpdate

class CRUDBreak(CRUDBase[GlobalBreak, GlobalBreakCreate, GlobalBreakUpdate]):
    pass

breaks = CRUDBreak(GlobalBreak)

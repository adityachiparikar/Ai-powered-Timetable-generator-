from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.api import deps
from app.crud.crud_break import breaks
from app.schemas.master_data_break import GlobalBreakCreate, GlobalBreakUpdate, GlobalBreakResponse

router = APIRouter()

@router.get("/", response_model=List[GlobalBreakResponse])
def read_breaks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(deps.get_current_active_superuser),
):
    return breaks.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=GlobalBreakResponse)
def create_break(
    *,
    db: Session = Depends(deps.get_db),
    break_in: GlobalBreakCreate,
    current_user = Depends(deps.get_current_active_superuser),
):
    return breaks.create(db, obj_in=break_in)

@router.put("/{break_id}", response_model=GlobalBreakResponse)
@router.put("/{break_id}/", response_model=GlobalBreakResponse, include_in_schema=False)
def update_break(
    *,
    db: Session = Depends(deps.get_db),
    break_id: str,
    break_in: GlobalBreakUpdate,
    current_user = Depends(deps.get_current_active_superuser),
):
    db_break = breaks.get(db, id=break_id)
    if not db_break:
        raise HTTPException(status_code=404, detail="Break not found")
    return breaks.update(db, db_obj=db_break, obj_in=break_in)

@router.delete("/{break_id}")
@router.delete("/{break_id}/", include_in_schema=False)
def delete_break(
    *,
    db: Session = Depends(deps.get_db),
    break_id: str,
    current_user = Depends(deps.get_current_active_superuser),
):
    db_break = breaks.get(db, id=break_id)
    if not db_break:
        raise HTTPException(status_code=404, detail="Break not found")
    breaks.remove(db, id=break_id)
    return {"status": "success"}

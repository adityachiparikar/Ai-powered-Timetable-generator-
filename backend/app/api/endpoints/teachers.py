from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.db.session import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.TeacherResponse])
def read_teachers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve teachers.
    """
    teachers = crud.teacher.get_multi(db, skip=skip, limit=limit)
    return teachers

@router.post("/", response_model=schemas.TeacherResponse)
def create_teacher(
    *,
    db: Session = Depends(get_db),
    teacher_in: schemas.TeacherCreate,
) -> Any:
    """
    Create new teacher.
    """
    from sqlalchemy.exc import IntegrityError
    try:
        teacher = crud.teacher.create(db=db, obj_in=teacher_in)
        return teacher
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"A teacher with the name or email already exists."
        )

@router.put("/{teacher_id}", response_model=schemas.TeacherResponse)
@router.put("/{teacher_id}/", response_model=schemas.TeacherResponse, include_in_schema=False)
def update_teacher(
    *,
    db: Session = Depends(get_db),
    teacher_id: str,
    teacher_in: schemas.TeacherUpdate,
) -> Any:
    """
    Update a teacher.
    """
    teacher = crud.teacher.get(db=db, id=teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    teacher = crud.teacher.update(db=db, db_obj=teacher, obj_in=teacher_in)
    return teacher

@router.delete("/{teacher_id}", response_model=schemas.TeacherResponse)
@router.delete("/{teacher_id}/", response_model=schemas.TeacherResponse, include_in_schema=False)
def delete_teacher(
    *,
    db: Session = Depends(get_db),
    teacher_id: str,
) -> Any:
    """
    Delete a teacher.
    """
    teacher = crud.teacher.get(db=db, id=teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    deleted_teacher = schemas.TeacherResponse.model_validate(teacher)

    db.query(models.TimetableEntry).filter(
        models.TimetableEntry.teacher_id == teacher.id
    ).delete(synchronize_session=False)

    db.query(models.Course).filter(
        models.Course.teacher_id == teacher.id
    ).update({"teacher_id": None}, synchronize_session=False)

    db.delete(teacher)
    db.commit()
    return deleted_teacher

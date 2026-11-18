from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.CourseResponse])
def read_courses(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    courses = crud.course.get_multi(db, skip=skip, limit=limit)
    return courses

@router.post("/", response_model=schemas.CourseResponse)
def create_course(
    *,
    db: Session = Depends(deps.get_db),
    course_in: schemas.CourseCreate,
) -> Any:
    """
    Create new course.
    """
    from sqlalchemy.exc import IntegrityError
    try:
        course = crud.course.create(db=db, obj_in=course_in)
        return course
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"A course with the code '{course_in.code}' already exists."
        )

@router.put("/{course_id}", response_model=schemas.CourseResponse)
@router.put("/{course_id}/", response_model=schemas.CourseResponse, include_in_schema=False)
def update_course(
    *,
    db: Session = Depends(deps.get_db),
    course_id: str,
    course_in: schemas.CourseUpdate,
) -> Any:
    course = crud.course.get(db=db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course = crud.course.update(db=db, db_obj=course, obj_in=course_in)
    return course

@router.delete("/{course_id}", response_model=schemas.CourseResponse)
@router.delete("/{course_id}/", response_model=schemas.CourseResponse, include_in_schema=False)
def delete_course(
    *,
    db: Session = Depends(deps.get_db),
    course_id: str,
) -> Any:
    course = crud.course.get(db=db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    deleted_course = schemas.CourseResponse.model_validate(course)
    db.query(models.TimetableEntry).filter(
        models.TimetableEntry.course_id == course.id
    ).delete(synchronize_session=False)
    db.delete(course)
    db.commit()
    return deleted_course

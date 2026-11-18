from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.StudentGroupResponse])
def read_student_groups(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    return crud.student_group.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=schemas.StudentGroupResponse)
def create_student_group(
    *,
    db: Session = Depends(deps.get_db),
    group_in: schemas.StudentGroupCreate,
) -> Any:
    return crud.student_group.create(db=db, obj_in=group_in)

@router.put("/{group_id}", response_model=schemas.StudentGroupResponse)
@router.put("/{group_id}/", response_model=schemas.StudentGroupResponse, include_in_schema=False)
def update_student_group(
    *,
    db: Session = Depends(deps.get_db),
    group_id: str,
    group_in: schemas.StudentGroupUpdate,
) -> Any:
    group = crud.student_group.get(db=db, id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Student Group not found")
    return crud.student_group.update(db=db, db_obj=group, obj_in=group_in)

@router.delete("/{group_id}", response_model=schemas.StudentGroupResponse)
@router.delete("/{group_id}/", response_model=schemas.StudentGroupResponse, include_in_schema=False)
def delete_student_group(
    *,
    db: Session = Depends(deps.get_db),
    group_id: str,
) -> Any:
    group = crud.student_group.get(db=db, id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Student Group not found")

    deleted_group = schemas.StudentGroupResponse.model_validate(group)
    batch_ids = [batch.id for batch in group.batches]

    course_filters = [models.Course.student_group_id == group.id]
    if batch_ids:
        course_filters.append(models.Course.batch_id.in_(batch_ids))

    affected_courses = db.query(models.Course).filter(or_(*course_filters)).all()
    affected_course_ids = [course.id for course in affected_courses]

    timetable_filters = []
    if affected_course_ids:
        timetable_filters.append(models.TimetableEntry.course_id.in_(affected_course_ids))
    if batch_ids:
        timetable_filters.append(models.TimetableEntry.batch_id.in_(batch_ids))

    if timetable_filters:
        db.query(models.TimetableEntry).filter(or_(*timetable_filters)).delete(synchronize_session=False)

    for course in affected_courses:
        if course.student_group_id == group.id:
            course.student_group_id = None
        if course.batch_id in batch_ids:
            course.batch_id = None

    db.delete(group)
    db.commit()
    return deleted_group

@router.post("/{group_id}/batches", response_model=schemas.BatchResponse)
@router.post("/{group_id}/batches/", response_model=schemas.BatchResponse, include_in_schema=False)
def create_batch(
    *,
    db: Session = Depends(deps.get_db),
    group_id: str,
    batch_in: schemas.BatchCreate,
) -> Any:
    group = crud.student_group.get(db=db, id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Student Group not found")
    return crud.student_group.create_batch(db=db, obj_in=batch_in, group_id=group_id)

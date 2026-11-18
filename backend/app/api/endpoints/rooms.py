from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app import crud, models, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.RoomResponse])
def read_rooms(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve rooms.
    """
    rooms = crud.room.get_multi(db, skip=skip, limit=limit)
    return rooms

@router.post("/", response_model=schemas.RoomResponse)
def create_room(
    *,
    db: Session = Depends(deps.get_db),
    room_in: schemas.RoomCreate,
) -> Any:
    """
    Create new room.
    """
    from sqlalchemy.exc import IntegrityError
    try:
        room = crud.room.create(db=db, obj_in=room_in)
        return room
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"A room with the name '{room_in.name}' already exists."
        )

@router.get("/{id}", response_model=schemas.RoomResponse)
@router.get("/{id}/", response_model=schemas.RoomResponse, include_in_schema=False)
def read_room(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
) -> Any:
    """
    Get room by ID.
    """
    room = crud.room.get(db=db, id=id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@router.put("/{id}", response_model=schemas.RoomResponse)
@router.put("/{id}/", response_model=schemas.RoomResponse, include_in_schema=False)
def update_room(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    room_in: schemas.RoomUpdate,
) -> Any:
    """
    Update a room.
    """
    room = crud.room.get(db=db, id=id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    room = crud.room.update(db=db, db_obj=room, obj_in=room_in)
    return room

@router.delete("/{id}", response_model=schemas.RoomResponse)
@router.delete("/{id}/", response_model=schemas.RoomResponse, include_in_schema=False)
def delete_room(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
) -> Any:
    """
    Delete a room.
    """
    room = crud.room.get(db=db, id=id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    deleted_room = schemas.RoomResponse.model_validate(room)
    db.query(models.TimetableEntry).filter(
        models.TimetableEntry.room_id == room.id
    ).delete(synchronize_session=False)
    db.delete(room)
    db.commit()
    return deleted_room

from typing import List, Any
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.student import StudentGroup, Batch
from app.schemas.student import StudentGroupCreate, StudentGroupUpdate, BatchCreate

class CRUDStudentGroup(CRUDBase[StudentGroup, StudentGroupCreate, StudentGroupUpdate]):
    def create_batch(self, db: Session, *, obj_in: BatchCreate, group_id: str) -> Batch:
        db_obj = Batch(
            name=obj_in.name,
            size=obj_in.size,
            student_group_id=group_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_batches(self, db: Session, group_id: str) -> List[Batch]:
        return db.query(Batch).filter(Batch.student_group_id == group_id).all()

    def create(self, db: Session, *, obj_in: StudentGroupCreate) -> StudentGroup:
        from sqlalchemy.exc import IntegrityError
        from fastapi import HTTPException
        try:
            # 1. Create the Group
            db_obj = StudentGroup(
                name=obj_in.name,
                size=obj_in.size,
                year_level=obj_in.year_level
            )
            db.add(db_obj)
            db.flush() # Generate ID without committing yet

            # 2. Auto-create 3 Batches
            # Simple Logic: Split size by 3. 
            batch_size = obj_in.size // 3
            # Adjust for remainder if necessary, but keep it simple for now as per "3 batches" rule.
            
            batch_names = ["b1", "b2", "b3"]
            for name in batch_names:
                batch = Batch(
                    name=name,
                    size=batch_size,
                    student_group_id=db_obj.id
                )
                db.add(batch)
            
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"A division with the name '{obj_in.name}' already exists."
            )

student_group = CRUDStudentGroup(StudentGroup)

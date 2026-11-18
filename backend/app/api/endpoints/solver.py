from fastapi import APIRouter, Depends, HTTPException
from typing import Any
import os
from app.core import security
from app.api import deps
from app.schemas.solver import SolverConfig

router = APIRouter()

@router.post("/generate", response_model=Any)
def generate_timetable(
    config: SolverConfig = None,
    term: str = "Fall 2025",
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Trigger the Solver Task in background.
    """
    # Lazy imports to avoid startup circular dependency or path issues
    from worker.tasks.solver_task import run_solver_task
    
    config_dict = config.dict() if config else None
    try:
        if os.getenv("SOLVER_ASYNC", "").lower() in {"1", "true", "yes"}:
            task = run_solver_task.delay(term, config_dict)
            return {"message": "Solver started", "task_id": str(task.id)}

        # The worker is optional in local setup. Running inline avoids queued
        # tasks sitting forever when Redis is up but Celery is not consuming.
        task = run_solver_task.apply(args=[term, config_dict])
        if task.failed():
            raise task.result
        return {
            "message": "Solver completed",
            "task_id": str(task.id),
            "status": "SUCCESS",
            "result": task.result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate timetable: {str(e)}")

@router.get("/status/{task_id}", response_model=Any)
def get_solver_status(task_id: str) -> Any:
    # Query Redis/Celery result backend
    from worker.celery_app import celery_app
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id, app=celery_app)
    
    # Standardize status
    status = result.status
    if status == "SUCCESS":
        return {"status": "SUCCESS", "result": result.result}
    elif status == "FAILURE":
        return {"status": "FAILURE", "error": str(result.result)}
    else:
        return {"status": status, "task_id": task_id}

@router.get("/logs/{task_id}", response_model=Any)
def get_solver_logs(task_id: str) -> Any:
    from app.services.solver.logger import SolverLogger
    logger = SolverLogger(task_id)
    return {"logs": logger.get_logs()}

@router.get("/timetable/{term}", response_model=Any)
def get_saved_timetable(
    term: str,
    db = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_superuser)
) -> Any:
    from app.models import TimetableEntry
    entries = db.query(TimetableEntry).filter(TimetableEntry.term == term).all()
    # Convert to expected format
    return {
        "entries": [
            {
                "course_id": str(e.course_id),
                "batch_id": str(e.batch_id) if e.batch_id else None,
                "teacher_id": str(e.teacher_id) if e.teacher_id else None,
                "room_id": str(e.room_id),
                "time_slot_id": str(e.time_slot_id),
                "day": e.day,
                "time_range": e.time_range,
                "student_group": e.student_group,
                "course_code": e.course_code,
                "room": e.room_name
            } for e in entries
        ]
    }

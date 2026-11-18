from fastapi import APIRouter, Depends, HTTPException
from typing import Any
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
    from worker.tasks.solver_task import run_solver_task
    config_dict = config.dict() if config else None
    task = run_solver_task.delay(term, config_dict)
    return {"message": "Solver started", "task_id": str(task.id)}

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

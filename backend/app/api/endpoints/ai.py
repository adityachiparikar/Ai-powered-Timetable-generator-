from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any
from sqlalchemy.orm import Session
from app.api import deps
from app.services.llm.nlp_service import NLPConstraintService
from app.services.timetable_change_service import TimetableChangeService

router = APIRouter()

class NLPRequest(BaseModel):
    text: str

class ChatRequest(BaseModel):
    message: str
    current_config: dict
    term: str = "Fall 2025"

class ApplyTimetableChangeRequest(BaseModel):
    proposal: dict

@router.post("/chat", response_model=Any)
def chat_soft_constraints(
    request: ChatRequest,
    db: Session = Depends(deps.get_db), # Add DB session
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Chat with the AI assistant about soft constraints and data issues.
    """
    service = NLPConstraintService()
    result = service.process_chat_request(request.message, request.current_config, db=db)
    
    # Execute Action if requested
    action = result.get("action")
    if action and action.get("type") in {"MOVE_GROUP_DAY_SESSIONS", "MOVE_TEACHER_DAY_SESSIONS"}:
        return TimetableChangeService(db).preview_change(action, term=request.term)

    if action and action.get("type") == "UPSERT_TEACHER_CONSTRAINT":
        from app.models import Teacher
        from app.models.master_data import TeacherConstraint
        from datetime import datetime
        params = action.get("params", {})
        teacher_name = params.get("teacher_name")
        
        teacher = db.query(Teacher).filter(Teacher.name == teacher_name).first()
        if teacher:
            # Parse times
            try:
                start_t = datetime.strptime(params["start_time"], "%H:%M").time()
                end_t = datetime.strptime(params["end_time"], "%H:%M").time()
                
                # Check for existing
                constraint = db.query(TeacherConstraint).filter(
                    TeacherConstraint.teacher_id == teacher.id,
                    TeacherConstraint.day_of_week == params.get("day_of_week")
                ).first()
                
                if not constraint:
                    constraint = TeacherConstraint(teacher_id=teacher.id)
                    db.add(constraint)
                
                constraint.day_of_week = params.get("day_of_week")
                constraint.start_time = start_t
                constraint.end_time = end_t
                constraint.is_available = params.get("is_available", False)
                
                db.commit()
                result["response"] += f" (Successfully updated schedule for {teacher_name})"
            except Exception as e:
                result["response"] += f" (Failed to update database: {str(e)})"
        else:
             result["response"] += f" (Could not find a teacher named '{teacher_name}')"

    return result

@router.post("/apply-timetable-change", response_model=Any)
def apply_timetable_change(
    request: ApplyTimetableChangeRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Apply a timetable change proposal after the user confirms it in the UI.
    """
    return TimetableChangeService(db).apply_change(request.proposal)

@router.post("/parse", response_model=Any)
def parse_constraint_text(
    request: NLPRequest,
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Parse a natural language constraint string using Ollama.
    """
    service = NLPConstraintService()
    result = service.parse_constraint(request.text)
    return result

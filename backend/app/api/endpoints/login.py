from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core import security
from app.models.user import User

router = APIRouter()

@router.post("/login/access-token")
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    # Minimal mock login for now until User CRUD is ready
    # In real app: authenticate_user(db, email, password)
    # user = db.query(User).filter(User.email == form_data.username).first()
    # if not user or not security.verify_password(form_data.password, user.hashed_password):
    #     raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # DEV MODE bypass
    if form_data.username == "admin@example.com" and form_data.password == "admin":
        return {
            "access_token": security.create_access_token(subject="admin_id"),
            "token_type": "bearer",
        }
    
    raise HTTPException(status_code=400, detail="Incorrect credentials")

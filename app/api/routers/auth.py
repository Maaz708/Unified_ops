# app/api/routers/auth.py
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.core.config import settings
from app.core.security import verify_password
from app.models.users import StaffUser

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_in: int


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate staff/owner by email and password. Returns a JWT.
    Frontend should set it as auth_token cookie (or use in Authorization header).
    """
    user = db.query(StaffUser).filter(StaffUser.email == payload.email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expires_minutes)
    payload_jwt = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "workspace_id": str(user.workspace_id),
        "exp": expires,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(
        payload_jwt,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return LoginResponse(
        token=token,
        expires_in=settings.access_token_expires_minutes * 60,
    )

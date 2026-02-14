# app/api/routers/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.dependencies.db import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    # Lightweight DB check
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
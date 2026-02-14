# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""


# For Neon / Render, keep pool small
engine = create_engine(
    str(settings.database_url),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def get_db_session() -> Session:
    """
    Utility for non-FastAPI contexts (e.g. scripts).
    Use the FastAPI dependency below inside routes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
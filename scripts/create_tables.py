"""
One-off script to create all database tables from SQLAlchemy models.
Run from project root: python -m scripts.create_tables
"""
import sys

# Add project root to path
sys.path.insert(0, "")

from sqlalchemy import text
from app.core.database import Base, engine
import app.models  # noqa: F401 - register all models with Base

if __name__ == "__main__":
    print("Creating all tables...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    print("Done.")

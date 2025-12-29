"""Database connection for local storage."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
import os
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Database file location
DB_DIR = Path.home() / ".p6_analyzer" / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE = DB_DIR / "p6_analyzer.db"

# Create engine
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


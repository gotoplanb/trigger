"""
API dependencies module.

This module provides dependencies for the FastAPI routes.
"""

from typing import Generator

from sqlalchemy.orm import Session

from app.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session.
    
    Yields:
        A SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

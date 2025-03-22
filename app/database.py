"""
Database configuration module.

This module handles database connection and session management.
"""

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base

logger = logging.getLogger(__name__)

# Check if we're running in test mode
TESTING = os.environ.get("TESTING", "").lower() == "true"

try:
    if TESTING:
        # Use in-memory SQLite for testing
        logger.info("Using in-memory SQLite database for testing")
        DB_URL = "sqlite:///:memory:"
        engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
    else:
        # Configure PostgreSQL engine for production
        DB_URL = settings.DATABASE_URL
        if DB_URL.startswith("postgres://"):
            DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

        logger.info("Connecting to PostgreSQL database")
        engine = create_engine(
            DB_URL,
            pool_size=10,  # Increased pool size
            max_overflow=20,  # Increased max overflow
            pool_timeout=30,  # Connection timeout in seconds
            pool_recycle=1800,  # Recycle connections after 30 minutes
            pool_pre_ping=True,  # Check connection validity before using
        )

    # Create SessionLocal class
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database connection established successfully")

except SQLAlchemyError as e:
    logger.error("Database connection failed: %s", str(e))
    raise


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This function should be called when the application starts.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error("Failed to create database tables: %s", str(e))
        raise


# Initialize the database if not testing
# For tests, we'll initialize in the fixtures
if not TESTING:
    init_db()

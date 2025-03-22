"""
Test configuration module.

This module provides pytest fixtures for testing.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.main import app
from app.api.dependencies import get_db


# Set testing mode
os.environ["TESTING"] = "true"

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db():
    """
    Database session fixture.

    Yields:
        SQLAlchemy session
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session for testing
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    """
    Test client fixture.

    Args:
        db: Database session fixture

    Yields:
        FastAPI TestClient
    """
    # Override the get_db dependency to use test db
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Reset dependency override
    app.dependency_overrides = {}
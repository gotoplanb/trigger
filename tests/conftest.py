"""
Test configuration module.

This module provides pytest fixtures for testing.
"""

# Set testing mode as early as possible
import os

os.environ["TESTING"] = "true"

import sys
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Mock CDC modules to prevent database connections during tests
sys.modules["psycopg"] = mock.MagicMock()
sys.modules["psycopg.rows"] = mock.MagicMock()
sys.modules["psycopg.sql"] = mock.MagicMock()
sys.modules["psycopg_pool"] = mock.MagicMock()

# Create and apply module mocks
event_processor_module = mock.MagicMock()
mock_event_processor = mock.MagicMock()
event_processor_class = mock.MagicMock(return_value=mock_event_processor)
event_processor_module.EventProcessor = event_processor_class

cdc_listener_module = mock.MagicMock()
mock_cdc_listener = mock.MagicMock()
cdc_listener_class = mock.MagicMock(return_value=mock_cdc_listener)
cdc_listener_module.CDCListener = cdc_listener_class

# Apply mocks to modules
sys.modules["app.events.processor"] = event_processor_module
sys.modules["app.cdc.listener"] = cdc_listener_module

# Import app dependencies after setting test mode and mocking
from app.api.dependencies import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.base import Base  # noqa: E402

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables before tests run
Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db():
    """
    Database session fixture.

    Yields:
        SQLAlchemy session
    """
    connection = engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


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

    with TestClient(app) as test_client:
        yield test_client

    # Reset dependency override
    app.dependency_overrides = {}

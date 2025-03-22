"""
SQLAlchemy base model module.

This module provides the base model for all SQLAlchemy models.
"""

import json
import os
from typing import Any

from sqlalchemy import String, TypeDecorator
from sqlalchemy.orm import declarative_base

# Determine if we're running in test mode
TESTING = os.environ.get("TESTING", "").lower() == "true"


# Custom JSON type for SQLite compatibility in tests
class JSONType(TypeDecorator):
    """
    Custom SQLAlchemy type for handling JSON in a database-agnostic way.
    """

    impl = String

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        """Convert Python object to JSON string for storage."""
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        """Convert stored JSON string to Python object."""
        if value is not None:
            return json.loads(value)
        return None


# Create a base class for all models
Base = declarative_base()

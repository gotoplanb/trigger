"""
Base model for SQLAlchemy models.

This module provides a base class for all SQLAlchemy ORM models.
"""

from sqlalchemy.ext.declarative import declarative_base

# Create a Base class for SQLAlchemy models
Base = declarative_base()

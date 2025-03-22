"""
Configuration settings module.

This module manages application-wide configuration settings using Pydantic.
"""

import os

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings.

    Attributes:
        DATABASE_URL: Database connection string for triggers database
        MONITORS_DATABASE_URL: Database connection string for monitors database
        API_V1_STR: API version prefix
        PROJECT_NAME: Name of the project
        REPLICATION_SLOT: PostgreSQL replication slot name
        PUBLICATION_NAME: PostgreSQL publication name
        NOTIFICATION_ENDPOINT: API endpoint to call on change events
    """

    # Required configuration with defaults for testing
    DATABASE_URL: str = Field(
        default="sqlite:///:memory:" if os.environ.get("TESTING") == "true" else None
    )
    MONITORS_DATABASE_URL: str = Field(
        default="sqlite:///:memory:" if os.environ.get("TESTING") == "true" else None
    )

    # Optional configuration with defaults
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Triggers API"
    REPLICATION_SLOT: str = "triggers_slot"
    PUBLICATION_NAME: str = "triggers_publication"
    NOTIFICATION_ENDPOINT: str = "http://localhost:8000/api/v1/notify"

    model_config = ConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()

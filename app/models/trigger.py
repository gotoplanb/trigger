"""
Database models for the triggers system.

This module defines SQLAlchemy ORM models for triggers and related entities.
"""

from datetime import UTC, datetime
import enum

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Table, JSON, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base


class ChangeType(str, enum.Enum):
    """
    Type of database change event.
    
    Attributes:
        INSERT: New record added
        UPDATE: Existing record modified
        DELETE: Record deleted
    """

    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


class EntityType(str, enum.Enum):
    """
    Type of database entity being monitored.
    
    Attributes:
        MONITOR: Monitor entity
        MONITOR_STATUS: MonitorStatus entity
        TAG: Tag entity
    """

    MONITOR = "monitor"
    MONITOR_STATUS = "monitor_status"
    TAG = "tag"


class Trigger(Base):  # pylint: disable=too-few-public-methods
    """
    Trigger model representing a configured trigger that watches for database changes.

    Attributes:
        id: Unique identifier
        name: Trigger name
        entity_type: Type of entity to watch (monitor, monitor_status, tag)
        change_types: Types of changes to watch for (insert, update, delete)
        filter_condition: Optional JSON condition to filter events
        endpoint: API endpoint to notify when trigger fires
        is_active: Whether the trigger is active
        created_at: When the trigger was created
        updated_at: When the trigger was last updated
        events: Relationship to trigger events
    """

    __tablename__ = "triggers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    entity_type = Column(Enum(EntityType), nullable=False)
    change_types = Column(JSON, nullable=False)  # JSON array of ChangeType values
    filter_condition = Column(JSON, nullable=True)  # Optional JSON condition 
    endpoint = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(UTC), 
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )
    
    events = relationship("TriggerEvent", back_populates="trigger")


class TriggerEvent(Base):  # pylint: disable=too-few-public-methods
    """
    Trigger event model representing a recorded change event.

    Attributes:
        id: Unique identifier
        trigger_id: Reference to the trigger
        entity_id: ID of the entity that changed
        change_type: Type of change (insert, update, delete)
        old_data: Previous state of the data (for updates/deletes)
        new_data: New state of the data (for inserts/updates)
        processed: Whether the event was processed
        response_status: HTTP status from notification endpoint
        created_at: When the event was recorded
        processed_at: When the event was processed
        trigger: Relationship to the parent trigger
    """

    __tablename__ = "trigger_events"

    id = Column(Integer, primary_key=True, index=True)
    trigger_id = Column(Integer, ForeignKey("triggers.id"))
    entity_id = Column(Integer, nullable=False)
    change_type = Column(Enum(ChangeType), nullable=False)
    old_data = Column(JSON, nullable=True)
    new_data = Column(JSON, nullable=True)
    processed = Column(Boolean, default=False)
    response_status = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    trigger = relationship("Trigger", back_populates="events")

"""
Pydantic schemas for the triggers API.

This module defines Pydantic schemas for API request and response validation.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field

from app.models.trigger import ChangeType, EntityType


class TriggerBase(BaseModel):
    """
    Base trigger schema with common attributes.
    """
    name: str
    entity_type: EntityType
    change_types: List[ChangeType]
    filter_condition: Optional[Dict[str, Any]] = None
    endpoint: str
    is_active: bool = True


class TriggerCreate(TriggerBase):
    """
    Schema for creating a new trigger.
    """
    pass


class TriggerUpdate(BaseModel):
    """
    Schema for updating an existing trigger.
    """
    name: Optional[str] = None
    entity_type: Optional[EntityType] = None
    change_types: Optional[List[ChangeType]] = None
    filter_condition: Optional[Dict[str, Any]] = None
    endpoint: Optional[str] = None
    is_active: Optional[bool] = None


class TriggerInDB(TriggerBase):
    """
    Schema for a trigger as stored in the database.
    """
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TriggerEventBase(BaseModel):
    """
    Base trigger event schema with common attributes.
    """
    entity_id: int
    change_type: ChangeType
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None


class TriggerEventCreate(TriggerEventBase):
    """
    Schema for creating a new trigger event.
    """
    trigger_id: int


class TriggerEventUpdate(BaseModel):
    """
    Schema for updating an existing trigger event.
    """
    processed: Optional[bool] = None
    response_status: Optional[int] = None
    processed_at: Optional[datetime] = None


class TriggerEventInDB(TriggerEventBase):
    """
    Schema for a trigger event as stored in the database.
    """
    id: int
    trigger_id: int
    processed: bool
    response_status: Optional[int] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DatabaseChangeNotification(BaseModel):
    """
    Schema for sending database change notifications to external services.
    """
    trigger_name: str
    entity_type: EntityType
    entity_id: int
    change_type: ChangeType
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now())

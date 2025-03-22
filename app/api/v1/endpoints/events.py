"""
API endpoints for managing trigger events.

This module provides FastAPI routes for retrieving trigger events.
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_db
from app.models.trigger import TriggerEvent, Trigger, ChangeType
from app.schemas.trigger import TriggerEventInDB

router = APIRouter()


@router.get("/", response_model=List[TriggerEventInDB])
async def read_events(
    skip: int = 0, 
    limit: int = 100, 
    trigger_id: Optional[int] = None,
    processed: Optional[bool] = None,
    change_type: Optional[ChangeType] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve trigger events with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        trigger_id: Filter by trigger ID
        processed: Filter by processed status
        change_type: Filter by change type
        db: Database session
        
    Returns:
        List of trigger event objects
    """
    query = db.query(TriggerEvent)
    
    # Apply filters if provided
    if trigger_id is not None:
        query = query.filter(TriggerEvent.trigger_id == trigger_id)
    if processed is not None:
        query = query.filter(TriggerEvent.processed == processed)
    if change_type is not None:
        query = query.filter(TriggerEvent.change_type == change_type)
        
    # Order by creation date, newest first
    query = query.order_by(TriggerEvent.created_at.desc())
    
    events = query.offset(skip).limit(limit).all()
    return events


@router.get("/{event_id}", response_model=TriggerEventInDB)
async def read_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific trigger event by ID.
    
    Args:
        event_id: Event ID
        db: Database session
        
    Returns:
        The trigger event object
    """
    event = (
        db.query(TriggerEvent)
        .filter(TriggerEvent.id == event_id)
        .first()
    )
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found"
        )
    return event


@router.get("/trigger/{trigger_id}", response_model=List[TriggerEventInDB])
async def read_trigger_events(
    trigger_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get events for a specific trigger.
    
    Args:
        trigger_id: Trigger ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of trigger event objects
    """
    # First check if trigger exists
    trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
    if trigger is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trigger with ID {trigger_id} not found"
        )
    
    events = (
        db.query(TriggerEvent)
        .filter(TriggerEvent.trigger_id == trigger_id)
        .order_by(TriggerEvent.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return events

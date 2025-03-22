"""
API endpoints for managing triggers.

This module provides FastAPI routes for CRUD operations on triggers.
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.trigger import Trigger, EntityType, ChangeType
from app.schemas.trigger import TriggerCreate, TriggerUpdate, TriggerInDB

router = APIRouter()


@router.get("/", response_model=List[TriggerInDB])
async def read_triggers(
    skip: int = 0, 
    limit: int = 100, 
    entity_type: Optional[EntityType] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve triggers with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        entity_type: Filter by entity type
        is_active: Filter by active status
        db: Database session
        
    Returns:
        List of trigger objects
    """
    query = db.query(Trigger)
    
    # Apply filters if provided
    if entity_type is not None:
        query = query.filter(Trigger.entity_type == entity_type)
    if is_active is not None:
        query = query.filter(Trigger.is_active == is_active)
        
    triggers = query.offset(skip).limit(limit).all()
    return triggers


@router.post("/", response_model=TriggerInDB, status_code=status.HTTP_201_CREATED)
async def create_trigger(
    trigger_in: TriggerCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new trigger.
    
    Args:
        trigger_in: Trigger creation data
        db: Database session
        
    Returns:
        The created trigger
    """
    # Check if trigger with the same name already exists
    existing_trigger = db.query(Trigger).filter(Trigger.name == trigger_in.name).first()
    if existing_trigger:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trigger with name '{trigger_in.name}' already exists"
        )
    
    # Convert trigger_in to model data
    trigger_data = trigger_in.model_dump()
    
    # Create new trigger
    db_trigger = Trigger(**trigger_data)
    db.add(db_trigger)
    db.commit()
    db.refresh(db_trigger)
    
    return db_trigger


@router.get("/{trigger_id}", response_model=TriggerInDB)
async def read_trigger(
    trigger_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific trigger by ID.
    
    Args:
        trigger_id: Trigger ID
        db: Database session
        
    Returns:
        The trigger object
    """
    trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
    if trigger is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trigger with ID {trigger_id} not found"
        )
    return trigger


@router.put("/{trigger_id}", response_model=TriggerInDB)
async def update_trigger(
    trigger_id: int,
    trigger_in: TriggerUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a trigger.
    
    Args:
        trigger_id: Trigger ID
        trigger_in: Trigger update data
        db: Database session
        
    Returns:
        The updated trigger
    """
    trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
    if trigger is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trigger with ID {trigger_id} not found"
        )
    
    # Update trigger fields from trigger_in
    update_data = trigger_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trigger, field, value)
    
    db.add(trigger)
    db.commit()
    db.refresh(trigger)
    
    return trigger


@router.delete("/{trigger_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trigger(
    trigger_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a trigger.
    
    Args:
        trigger_id: Trigger ID
        db: Database session
    """
    trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
    if trigger is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trigger with ID {trigger_id} not found"
        )
    
    db.delete(trigger)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{trigger_id}/activate", response_model=TriggerInDB)
async def activate_trigger(
    trigger_id: int,
    db: Session = Depends(get_db)
):
    """
    Activate a trigger.
    
    Args:
        trigger_id: Trigger ID
        db: Database session
        
    Returns:
        The activated trigger
    """
    trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
    if trigger is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trigger with ID {trigger_id} not found"
        )
    
    trigger.is_active = True
    db.add(trigger)
    db.commit()
    db.refresh(trigger)
    
    return trigger


@router.post("/{trigger_id}/deactivate", response_model=TriggerInDB)
async def deactivate_trigger(
    trigger_id: int,
    db: Session = Depends(get_db)
):
    """
    Deactivate a trigger.
    
    Args:
        trigger_id: Trigger ID
        db: Database session
        
    Returns:
        The deactivated trigger
    """
    trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
    if trigger is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trigger with ID {trigger_id} not found"
        )
    
    trigger.is_active = False
    db.add(trigger)
    db.commit()
    db.refresh(trigger)
    
    return trigger

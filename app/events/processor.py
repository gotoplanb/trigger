"""
Event processor module.

This module handles processing of change events detected by the CDC listener.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Dict, Any, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.trigger import Trigger, TriggerEvent, ChangeType, EntityType
from app.schemas.trigger import DatabaseChangeNotification, TriggerEventCreate, TriggerEventUpdate

logger = logging.getLogger(__name__)


class EventProcessor:
    """
    Processor for database change events.
    
    This class handles the processing of change events, including:
    1. Matching events against configured triggers
    2. Recording events in the database
    3. Sending notifications to configured endpoints
    """
    
    def __init__(self):
        """
        Initialize the event processor.
        """
        self.client = httpx.AsyncClient(timeout=30.0)  # 30 second timeout
    
    def _get_db(self) -> Session:
        """
        Get a database session.
        
        Returns:
            A SQLAlchemy database session
        """
        db = SessionLocal()
        try:
            return db
        except Exception:
            db.close()
            raise
    
    async def process_change_event(self, event: Dict[str, Any]):
        """
        Process a change event from the CDC listener.
        
        Args:
            event: The change event to process
        """
        try:
            # Get matching triggers for this event
            matching_triggers = self._find_matching_triggers(event)
            
            if not matching_triggers:
                logger.debug("No matching triggers for event: %s", event)
                return
            
            # Process each matching trigger
            for trigger in matching_triggers:
                await self._process_trigger(trigger, event)
                
        except Exception as e:
            logger.error("Error processing change event: %s", str(e))
    
    def _find_matching_triggers(self, event: Dict[str, Any]) -> List[Trigger]:
        """
        Find triggers that match the given event.
        
        Args:
            event: The change event to match
            
        Returns:
            List of matching Trigger objects
        """
        entity_type = event['entity_type']
        change_type = event['change_type']
        
        db = self._get_db()
        try:
            # Query for active triggers matching the entity type and change type
            triggers = db.query(Trigger).filter(
                Trigger.is_active == True,
                Trigger.entity_type == entity_type,
                Trigger.change_types.contains(json.dumps([change_type]))
            ).all()
            
            # Further filter based on filter_condition if present
            matching_triggers = []
            for trigger in triggers:
                if self._check_filter_condition(trigger, event):
                    matching_triggers.append(trigger)
            
            return matching_triggers
        finally:
            db.close()
    
    def _check_filter_condition(self, trigger: Trigger, event: Dict[str, Any]) -> bool:
        """
        Check if the event matches the trigger's filter condition.
        
        Args:
            trigger: The trigger to check
            event: The change event to check
            
        Returns:
            True if the event matches the filter condition, False otherwise
        """
        # If no filter condition, always match
        if not trigger.filter_condition:
            return True
        
        try:
            # Get the data to check against the filter
            data = event.get('new_data') or event.get('old_data') or {}
            
            # Basic implementation - check if all filter conditions match
            # For more complex filtering, this could be expanded
            for key, value in trigger.filter_condition.items():
                if key not in data or data[key] != value:
                    return False
            
            return True
        except Exception as e:
            logger.error("Error checking filter condition: %s", str(e))
            return False  # Fail safe - don't match if we can't evaluate
    
    async def _process_trigger(self, trigger: Trigger, event: Dict[str, Any]):
        """
        Process a trigger for a matching event.
        
        Args:
            trigger: The matching trigger
            event: The change event to process
        """
        db = self._get_db()
        try:
            # Create an event record
            entity_id = self._get_entity_id(event)
            trigger_event = TriggerEvent(
                trigger_id=trigger.id,
                entity_id=entity_id,
                change_type=event['change_type'],
                old_data=event.get('old_data'),
                new_data=event.get('new_data'),
                processed=False
            )
            
            db.add(trigger_event)
            db.commit()
            db.refresh(trigger_event)
            
            # Send notification to the endpoint
            response_status = await self._send_notification(trigger, trigger_event, event)
            
            # Update the event record with the response status
            update_data = TriggerEventUpdate(
                processed=True,
                response_status=response_status,
                processed_at=datetime.now(UTC)
            )
            
            for key, value in update_data.model_dump(exclude_unset=True).items():
                setattr(trigger_event, key, value)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error("Error processing trigger %s: %s", trigger.id, str(e))
        finally:
            db.close()
    
    def _get_entity_id(self, event: Dict[str, Any]) -> int:
        """
        Extract the entity ID from the event data.
        
        Args:
            event: The change event
            
        Returns:
            The entity ID
        """
        # First try to get ID from new_data, then from old_data
        data = event.get('new_data') or event.get('old_data') or {}
        
        # Look for 'id' field
        entity_id = data.get('id')
        if entity_id is not None:
            return entity_id
        
        # If no ID found, raise an error
        raise ValueError(f"Could not determine entity ID from event data: {data}")
    
    async def _send_notification(self, 
                             trigger: Trigger, 
                             trigger_event: TriggerEvent, 
                             event: Dict[str, Any]) -> int:
        """
        Send a notification to the trigger's endpoint.
        
        Args:
            trigger: The trigger being processed
            trigger_event: The trigger event record
            event: The original change event
            
        Returns:
            HTTP status code from the notification endpoint
        """
        try:
            # Prepare the notification payload
            notification = DatabaseChangeNotification(
                trigger_name=trigger.name,
                entity_type=event['entity_type'],
                entity_id=trigger_event.entity_id,
                change_type=event['change_type'],
                old_data=event.get('old_data'),
                new_data=event.get('new_data'),
                timestamp=trigger_event.created_at
            )
            
            # Send the notification to the endpoint
            response = await self.client.post(
                trigger.endpoint,
                json=notification.model_dump(),
                headers={"Content-Type": "application/json"}
            )
            
            status_code = response.status_code
            
            if 200 <= status_code < 300:
                logger.info("Successfully sent notification for trigger %s: %s", 
                         trigger.id, status_code)
            else:
                logger.warning("Failed to send notification for trigger %s: %s", 
                            trigger.id, status_code)
            
            return status_code
            
        except httpx.HTTPError as e:
            logger.error("HTTP error sending notification for trigger %s: %s", 
                      trigger.id, str(e))
            return 500  # Internal server error
        
        except Exception as e:
            logger.error("Error sending notification for trigger %s: %s", 
                      trigger.id, str(e))
            return 500  # Internal server error
    
    async def close(self):
        """
        Close resources used by the event processor.
        """
        await self.client.aclose()

"""
Change data capture listener module.

This module implements the listener for database changes.
"""

import asyncio
import logging
import threading
from typing import Dict, Any, List, Optional

from app.cdc.connection import CDCConnection
from app.events.processor import EventProcessor

logger = logging.getLogger(__name__)


class CDCListener:
    """
    Listener for database changes using PostgreSQL logical replication.
    
    This class sets up a background thread to listen for database changes
    and processes them through the event processor.
    """
    
    def __init__(self, event_processor: EventProcessor):
        """
        Initialize the CDC listener.
        
        Args:
            event_processor: The event processor to handle detected changes
        """
        self.event_processor = event_processor
        self.cdc_connection = None
        self.listener_thread = None
        self.is_running = False
    
    def start(self):
        """
        Start the CDC listener in a background thread.
        """
        if self.is_running:
            logger.warning("CDC listener is already running")
            return
        
        self.is_running = True
        self.cdc_connection = CDCConnection()
        
        # Start the listener in a separate thread
        self.listener_thread = threading.Thread(
            target=self._run_listener,
            daemon=True  # Make thread a daemon so it exits when main thread exits
        )
        self.listener_thread.start()
        
        logger.info("Started CDC listener thread")
    
    def _run_listener(self):
        """
        Run the CDC listener and process changes.
        
        This method runs in a separate thread and calls the event processor
        for each change event received.
        """
        try:
            logger.info("Starting CDC replication")
            self.cdc_connection.start_replication(self._process_change_event)
        except Exception as e:
            logger.error("CDC listener thread error: %s", str(e))
            self.is_running = False
    
    def _process_change_event(self, event: Dict[str, Any]):
        """
        Process a change event from the CDC connection.
        
        Args:
            event: The change event to process
        """
        try:
            # Create an async task to process the event
            asyncio.run(self.event_processor.process_change_event(event))
        except Exception as e:
            logger.error("Error processing change event: %s", str(e))
    
    def stop(self):
        """
        Stop the CDC listener and clean up resources.
        """
        if not self.is_running:
            logger.warning("CDC listener is not running")
            return
        
        self.is_running = False
        
        if self.cdc_connection:
            self.cdc_connection.stop_replication()
        
        # Wait for the listener thread to finish
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=5)  # Wait up to 5 seconds
            
        logger.info("Stopped CDC listener")

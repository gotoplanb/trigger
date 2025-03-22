"""
PostgreSQL CDC connection module.

This module handles the logical replication connection to the PostgreSQL database.
"""

import json
import logging
from typing import Any, Callable, Dict

import psycopg
from psycopg import connection, sql
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.core.config import settings
from app.models.trigger import ChangeType, EntityType

logger = logging.getLogger(__name__)


class CDCConnection:
    """
    PostgreSQL CDC connection handler using logical replication.

    This class manages the connection to the PostgreSQL database for CDC,
    creates the necessary replication slot and publication, and processes
    incoming change events.
    """

    def __init__(self, slot_name: str = None, publication_name: str = None):
        """
        Initialize the CDC connection.

        Args:
            slot_name: Name of the replication slot to create or use
            publication_name: Name of the publication to create or use
        """
        self.slot_name = slot_name or settings.REPLICATION_SLOT
        self.publication_name = publication_name or settings.PUBLICATION_NAME
        self.conn = None
        self.pool = None
        self._setup_pool()
        self._create_publication_and_slot()

    def _setup_pool(self):
        """
        Set up the connection pool.
        """
        db_url = settings.MONITORS_DATABASE_URL

        # Ensure the URL starts with postgresql://
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        self.pool = ConnectionPool(db_url, min_size=1, max_size=5)

    def _get_connection(self, replication=False) -> connection:
        """
        Get a PostgreSQL connection.

        Args:
            replication: Whether to create a replication connection

        Returns:
            PostgreSQL connection object
        """
        db_url = settings.MONITORS_DATABASE_URL

        # Ensure the URL starts with postgresql://
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        try:
            if replication:
                # For replication connections, we need to create a special connection
                # with replication=True parameter
                conn_params = {
                    "replication": "database",
                }
                conn = psycopg.connect(db_url, **conn_params)
                return conn
            else:
                # Use the connection pool for regular connections
                return self.pool.getconn()
        except Exception as e:
            logger.error("Failed to connect to PostgreSQL: %s", str(e))
            raise

    def _create_publication_and_slot(self):
        """
        Create the publication and replication slot if they don't exist.
        """
        try:
            with self.pool.connection() as conn:
                conn.row_factory = dict_row

                # Check if publication exists
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT 1 FROM pg_publication WHERE pubname = %s",
                        (self.publication_name,),
                    )
                    publication_exists = cursor.fetchone() is not None

                    if not publication_exists:
                        tables = [
                            "public.monitor",
                            "public.monitor_statuses",
                            "public.tags",
                            "public.monitor_tags",
                        ]
                        tables_str = ", ".join(tables)
                        cursor.execute(
                            sql.SQL("CREATE PUBLICATION {} FOR TABLE {}").format(
                                sql.Identifier(self.publication_name),
                                sql.SQL(tables_str),
                            )
                        )
                        logger.info("Created publication %s", self.publication_name)

                    # Check if replication slot exists
                    cursor.execute(
                        "SELECT 1 FROM pg_replication_slots WHERE slot_name = %s",
                        (self.slot_name,),
                    )
                    slot_exists = cursor.fetchone() is not None

                # If slot doesn't exist, create it with a replication connection
                if not slot_exists:
                    repl_conn = self._get_connection(replication=True)
                    try:
                        with repl_conn.cursor() as repl_cursor:
                            repl_cursor.execute(
                                "SELECT pg_create_logical_replication_slot(%s, 'wal2json')",
                                (self.slot_name,),
                            )
                            logger.info("Created replication slot %s", self.slot_name)
                    finally:
                        repl_conn.close()

        except Exception as e:
            logger.error("Failed to create publication or slot: %s", str(e))
            raise

    def start_replication(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Start the replication process to receive change events.

        Args:
            callback: Function to call with each change event
        """
        try:
            self.conn = self._get_connection(replication=True)

            with self.conn.cursor() as cursor:
                # Start the replication process
                cursor.execute(
                    "START_REPLICATION SLOT %s LOGICAL 0/0 ("
                    "\"pretty-print\" '1', \"format-version\" '2')",
                    (self.slot_name,),
                )

                logger.info("Started replication from slot %s", self.slot_name)

                # Process messages as they arrive
                self._process_replication_stream(cursor, callback)

        except Exception as e:
            logger.error("Replication error: %s", str(e))
            if self.conn:
                self.conn.close()
            raise

    def _process_replication_stream(
        self,
        cursor: psycopg.Cursor,
        callback: Callable[[Dict[str, Any]], None],
    ):
        """
        Process the replication stream and call the callback with change events.

        Args:
            cursor: Replication cursor
            callback: Function to call with each change event
        """
        try:
            # Process messages until stopped
            while True:
                # Read WAL data (timeout is in seconds)
                msg = cursor.read(10)

                if msg is not None:
                    # Parse the WAL message
                    payload = json.loads(msg.data)

                    # Process each change in the message
                    for change in payload.get("change", []):
                        table_name = change.get("table")

                        # Map table to entity type
                        entity_type = None
                        if table_name == "monitor":
                            entity_type = EntityType.MONITOR
                        elif table_name == "monitor_statuses":
                            entity_type = EntityType.MONITOR_STATUS
                        elif table_name == "tags":
                            entity_type = EntityType.TAG
                        else:
                            # Skip tables we don't care about
                            continue

                        # Get the change type
                        kind = change.get("kind")
                        if kind == "insert":
                            change_type = ChangeType.INSERT
                            old_data = None
                            new_data = change.get("columnvalues", {})
                        elif kind == "update":
                            change_type = ChangeType.UPDATE
                            old_data = dict(
                                zip(
                                    change.get("columnnames", []),
                                    change.get("oldkeys", {}).get("keyvalues", []),
                                )
                            )
                            new_data = dict(
                                zip(
                                    change.get("columnnames", []),
                                    change.get("columnvalues", []),
                                )
                            )
                        elif kind == "delete":
                            change_type = ChangeType.DELETE
                            old_data = dict(
                                zip(
                                    change.get("oldkeys", {}).get("keynames", []),
                                    change.get("oldkeys", {}).get("keyvalues", []),
                                )
                            )
                            new_data = None
                        else:
                            continue

                        # Create change event object
                        event = {
                            "entity_type": entity_type,
                            "change_type": change_type,
                            "old_data": old_data,
                            "new_data": new_data,
                            "table_name": table_name,
                        }

                        # Pass the event to the callback
                        callback(event)

                    # Send feedback to the server to acknowledge the message
                    cursor.send_feedback(flush_lsn=msg.data_start)

        except Exception as e:
            logger.error("Error processing replication stream: %s", str(e))
            raise

    def stop_replication(self):
        """
        Stop the replication process and close the connection.
        """
        if self.conn:
            try:
                self.conn.close()
                logger.info("Stopped replication and closed connection")
            except Exception as e:
                logger.error("Error stopping replication: %s", str(e))
            finally:
                self.conn = None

        if self.pool:
            try:
                self.pool.close()
                logger.info("Closed connection pool")
            except Exception as e:
                logger.error("Error closing connection pool: %s", str(e))

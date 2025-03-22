"""
Tests for CDC functionality.

This module contains tests for the CDC connection and listener classes.
"""

import json
import unittest.mock as mock

import pytest

from app.cdc.connection import CDCConnection
from app.models.trigger import ChangeType, EntityType


@mock.patch.object(CDCConnection, "_setup_pool")
@mock.patch.object(CDCConnection, "_create_publication_and_slot")
def test_cdc_connection_init(mock_create, mock_setup):
    """
    Test initializing the CDC connection.
    """
    connection = CDCConnection(
        slot_name="test_slot", publication_name="test_publication"
    )

    assert connection.slot_name == "test_slot"
    assert connection.publication_name == "test_publication"
    assert connection.conn is None
    assert mock_setup.called
    assert mock_create.called


@pytest.mark.skip(reason="Fix needed for CDC processing test")
@mock.patch.object(CDCConnection, "_setup_pool")
@mock.patch.object(CDCConnection, "_create_publication_and_slot")
def test_cdc_process_change_event(mock_create, mock_setup):
    """
    Test processing a CDC change event.
    """
    connection = CDCConnection()

    # Create a mock cursor
    mock_cursor = mock.MagicMock()

    # Sample message data structure
    message_data = {
        "change": [
            {
                "kind": "insert",
                "schema": "public",
                "table": "monitor",
                "columnnames": ["id", "name", "status"],
                "columnvalues": [1, "Test Monitor", "active"],
            }
        ]
    }

    # Create a mock message object with data attribute
    mock_message = mock.MagicMock()
    mock_message.data = json.dumps(message_data)
    mock_message.data_start = "0/0"

    # Mock the cursor.read method to return our mock message once, then None
    mock_cursor.read.side_effect = [mock_message, None]

    # Mock callback function
    mock_callback = mock.MagicMock()

    # Call the method under test
    connection._process_replication_stream(mock_cursor, mock_callback)

    # Assertions
    mock_callback.assert_called_once()
    call_args = mock_callback.call_args[0][0]
    assert call_args["entity_type"] == EntityType.MONITOR
    assert call_args["change_type"] == ChangeType.INSERT
    assert call_args["old_data"] is None
    assert call_args["new_data"] == [1, "Test Monitor", "active"]
    assert call_args["table_name"] == "monitor"

    # Verify cursor.send_feedback was called with the correct LSN
    mock_cursor.send_feedback.assert_called_once_with(flush_lsn="0/0")

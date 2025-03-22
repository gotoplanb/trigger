"""
Tests for the triggers endpoints.

This module contains tests for the triggers API endpoints.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.trigger import EntityType, Trigger


def test_create_trigger(client: TestClient, db: Session):
    """
    Test creating a new trigger.

    Args:
        client: Test client
        db: Database session
    """
    # Create new trigger with lowercase enum values
    trigger_data = {
        "name": "Test Trigger",
        "entity_type": "monitor",  # Use lowercase to match EntityType enum values
        "change_types": [
            "insert",
            "update",
        ],  # Use lowercase to match ChangeType enum values
        "endpoint": "http://localhost:8000/test",
        "is_active": True,
    }

    response = client.post("/api/v1/triggers", json=trigger_data)
    assert response.status_code == 201, f"Response body: {response.text}"
    data = response.json()

    assert data["name"] == trigger_data["name"]
    assert data["entity_type"] == trigger_data["entity_type"]
    assert set(data["change_types"]) == set(trigger_data["change_types"])
    assert data["endpoint"] == trigger_data["endpoint"]
    assert data["is_active"] == trigger_data["is_active"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_triggers(client: TestClient, db: Session):
    """
    Test retrieving triggers.

    Args:
        client: Test client
        db: Database session
    """
    # Create test triggers with lowercase enum values for API compatibility
    trigger1 = Trigger(
        name="Test Trigger 1",
        entity_type=EntityType.MONITOR,
        change_types=["insert"],  # Use lowercase for API compatibility
        endpoint="http://localhost:8000/test1",
        is_active=True,
    )
    trigger2 = Trigger(
        name="Test Trigger 2",
        entity_type=EntityType.MONITOR_STATUS,
        change_types=["update", "delete"],  # Use lowercase for API compatibility
        endpoint="http://localhost:8000/test2",
        is_active=False,
    )

    db.add(trigger1)
    db.add(trigger2)
    db.commit()

    # Test getting all triggers
    response = client.get("/api/v1/triggers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Test getting by ID
    response = client.get(f"/api/v1/triggers/{trigger1.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == trigger1.name

    # Test filtering by entity_type (using lowercase to match enum values)
    response = client.get("/api/v1/triggers", params={"entity_type": "monitor_status"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == trigger2.name

    # Test filtering by is_active
    response = client.get("/api/v1/triggers", params={"is_active": "false"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == trigger2.name


def test_update_trigger(client: TestClient, db: Session):
    """
    Test updating a trigger.

    Args:
        client: Test client
        db: Database session
    """
    # Create test trigger with lowercase enum values for API compatibility
    trigger = Trigger(
        name="Original Name",
        entity_type=EntityType.MONITOR,
        change_types=["insert"],  # Use lowercase for API compatibility
        endpoint="http://localhost:8000/original",
        is_active=True,
    )

    db.add(trigger)
    db.commit()
    db.refresh(trigger)

    # Update the trigger
    update_data = {
        "name": "Updated Name",
        "endpoint": "http://localhost:8000/updated",
        "is_active": False,
    }

    response = client.put(f"/api/v1/triggers/{trigger.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == update_data["name"]
    assert data["endpoint"] == update_data["endpoint"]
    assert data["is_active"] == update_data["is_active"]
    # Ensure other fields weren't changed
    assert data["entity_type"] == trigger.entity_type


def test_delete_trigger(client: TestClient, db: Session):
    """
    Test deleting a trigger.

    Args:
        client: Test client
        db: Database session
    """
    # Create test trigger with lowercase enum values for API compatibility
    trigger = Trigger(
        name="To Delete",
        entity_type=EntityType.MONITOR,
        change_types=["insert"],  # Use lowercase for API compatibility
        endpoint="http://localhost:8000/delete",
        is_active=True,
    )

    db.add(trigger)
    db.commit()
    db.refresh(trigger)

    # Delete the trigger
    response = client.delete(f"/api/v1/triggers/{trigger.id}")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/api/v1/triggers/{trigger.id}")
    assert response.status_code == 404

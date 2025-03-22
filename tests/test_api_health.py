"""
Tests for the health check endpoint.

This module contains tests for the health check API endpoint.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """
    Test the health check endpoint.
    
    Args:
        client: Test client
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
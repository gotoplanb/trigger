"""
Health check endpoint for the API.

This module provides a simple health check endpoint.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """
    Health check response model.
    """

    status: str
    version: str = "0.1.0"


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Perform a health check.

    Returns:
        Health check status
    """
    return HealthResponse(status="ok")

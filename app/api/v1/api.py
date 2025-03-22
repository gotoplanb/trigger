"""
API router module.

This module sets up the main API router with all endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import triggers, events, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    triggers.router, prefix="/triggers", tags=["triggers"]
)
api_router.include_router(
    events.router, prefix="/events", tags=["events"]
)
api_router.include_router(
    health.router, prefix="/health", tags=["health"]
)

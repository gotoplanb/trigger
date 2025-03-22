"""
Main application module.

This module sets up the FastAPI application.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.cdc.listener import CDCListener
from app.core.config import settings
from app.events.processor import EventProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# Event processor instance to be shared
event_processor = EventProcessor()

# CDC listener instance to be started/stopped with the application
cdc_listener = CDCListener(event_processor)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    This function handles startup and shutdown events for the application.
    """
    import os

    # Startup - but only if not in testing mode
    if os.environ.get("TESTING") != "true":
        logger.info("Starting CDC listener")
        cdc_listener.start()

    yield

    # Shutdown - but only if not in testing mode
    if os.environ.get("TESTING") != "true":
        logger.info("Stopping CDC listener")
        cdc_listener.stop()

        # Close HTTP client for event processor
        await event_processor.close()


# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        Welcome message
    """
    return {"message": f"Welcome to {settings.PROJECT_NAME}!"}

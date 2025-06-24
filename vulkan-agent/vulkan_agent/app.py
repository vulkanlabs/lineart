import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import config_manager
from .routers import chat, config, sessions


def setup_logging():
    """Configure logging for the application."""
    # Get log level from environment variable, default to INFO for development
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set specific logger levels for FastAPI and uvicorn
    logging.getLogger("fastapi").setLevel(
        logging.DEBUG if log_level == "DEBUG" else logging.INFO
    )
    logging.getLogger("uvicorn").setLevel(
        logging.DEBUG if log_level == "DEBUG" else logging.INFO
    )
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    # Create logger for our application
    logger = logging.getLogger("vulkan_agent")
    logger.info(f"Logging configured with level: {log_level}")

    return logger


# Initialize logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management.

    Handles startup and shutdown tasks:
    - Startup: Initialize components and check configuration
    - Shutdown: Clean up resources (if needed in future)
    """
    # Startup tasks
    logger.info("Starting Vulkan Agent service...")

    if config_manager.is_configured():
        logger.info("✓ Agent configuration loaded successfully")
    else:
        logger.warning("⚠ Agent configuration not found - please configure via API")

    yield

    # Shutdown tasks (placeholder for future cleanup)
    # Could include: database connections, background tasks, etc.
    logger.info("Shutting down Vulkan Agent service...")
    pass


app = FastAPI(
    title="Vulkan AI Agent",
    description="AI Agent service for Vulkan platform - provides conversational assistance for users",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(config.router)
app.include_router(chat.router)
app.include_router(sessions.router)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify the service is running."""
    return {
        "status": "healthy",
        "service": "vulkan-agent",
        "version": "0.1.0",
        "configured": config_manager.is_configured(),
    }


@app.get("/")
async def root():
    """Root endpoint with service status and discovery information."""
    return {
        "service": "vulkan-agent",
        "description": "AI Agent service for Vulkan platform",
        "version": "0.1.0",
        "status": "healthy" if config_manager.is_configured() else "not_configured",
        "configured": config_manager.is_configured(),
        "documentation": {
            "interactive": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json",
        },
        "health_check": "/health",
    }

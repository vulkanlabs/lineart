from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import config_manager
from .routers import chat, config, sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management.

    Handles startup and shutdown tasks:
    - Startup: Initialize components and check configuration
    - Shutdown: Clean up resources (if needed in future)
    """
    # Startup tasks
    if config_manager.is_configured():
        print("✓ Agent configuration loaded successfully")
    else:
        print("⚠ Agent configuration not found - please configure via API")

    yield

    # Shutdown tasks (placeholder for future cleanup)
    # Could include: database connections, background tasks, etc.
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

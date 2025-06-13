import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Vulkan AI Agent",
    description="AI Agent service for Vulkan platform - provides conversational assistance for users",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify the service is running."""
    return {"status": "healthy", "service": "vulkan-agent", "version": "0.1.0"}


@app.get("/")
async def root():
    """Root endpoint with basic service information."""
    return {
        "service": "vulkan-agent",
        "description": "AI Agent service for Vulkan platform",
        "version": "0.1.0",
        "health_endpoint": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        "vulkan_agent.app:app",
        host=host,
        port=port,
        reload=True,
    )

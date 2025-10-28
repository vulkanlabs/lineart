import logging
import sys

from data_router import auth_router
from data_router import router as data_router
from fastapi import FastAPI, Request
from fipe_router import router as fipe_router

# Create the main FastAPI application
app = FastAPI(
    title="Mock Data Server",
    version="1.0.0",
    description="Combined server with data lookup and FIPE vehicle pricing endpoints",
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
)
logger = logging.getLogger("uvicorn.error")
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

# Include the routers
app.include_router(data_router)
app.include_router(auth_router)
app.include_router(fipe_router)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mock-data-server",
        "endpoints": {
            "data_server": ["/data/scr", "/data/serasa"],
            "fipe": ["/fipe/"],
            "health": ["/health"],
        },
    }


@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "Mock Data Server API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Incoming request: {request.method} {request.url}")
    try:
        body = await request.json()
        logging.info(f"Request body: {body}")
    except Exception:
        logging.error("Failed to parse request body")

    response = await call_next(request)
    return response

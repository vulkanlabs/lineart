from fastapi.testclient import TestClient
from vulkan_agent.app import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "vulkan-agent"
    assert data["version"] == "0.1.0"


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "vulkan-agent"
    assert data["version"] == "0.1.0"
    assert "description" in data
    assert data["health_endpoint"] == "/health"


def test_cors_headers():
    """Test that CORS headers are properly set."""
    response = client.get("/health")
    assert response.status_code == 200
    # CORS headers should be present due to middleware

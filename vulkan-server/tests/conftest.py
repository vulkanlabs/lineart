from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from vulkan_server.app import app
from vulkan_server.dependencies import get_policy_service


@pytest.fixture
def mock_policy_service():
    """Create a mock PolicyService."""
    return MagicMock()


@pytest.fixture
def client(mock_policy_service):
    """Create a test client with mocked dependencies."""

    def override_get_policy_service():
        return mock_policy_service

    app.dependency_overrides[get_policy_service] = override_get_policy_service
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()

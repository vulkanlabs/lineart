"""Tests for agent configuration management."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from vulkan_agent.app import app
from vulkan_agent.config import ConfigManager
from vulkan_agent.llm import LLMProvider
from vulkan_agent.schemas import AgentConfigRequest

client = TestClient(app)


class TestConfigManager:
    """Test core ConfigManager functionality."""

    def test_update_config(self):
        """Test updating configuration."""
        manager = ConfigManager()

        config_request = AgentConfigRequest(
            provider=LLMProvider.OPENAI, api_key="sk-test123", model="gpt-4o-mini"
        )

        updated_config = manager.update_config(config_request)

        assert updated_config.provider == LLMProvider.OPENAI
        assert updated_config.model == "gpt-4o-mini"
        assert updated_config.api_key_configured is True
        assert manager.is_configured()

    def test_get_llm_config_after_update(self):
        """Test getting LLM configuration after update."""
        manager = ConfigManager()

        config_request = AgentConfigRequest(
            provider=LLMProvider.ANTHROPIC,
            api_key="sk-ant-test123",
            model="claude-3-5-haiku-20241022",
        )
        manager.update_config(config_request)

        llm_config = manager.get_llm_config()
        assert llm_config is not None
        assert llm_config.provider == LLMProvider.ANTHROPIC
        assert llm_config.api_key == "sk-ant-test123"
        assert llm_config.model == "claude-3-5-haiku-20241022"


class TestConfigEndpoints:
    """Test configuration API endpoints."""

    def test_get_config_not_configured(self):
        """Test getting configuration when not configured."""
        with patch("vulkan_agent.routers.config.config_manager") as mock_manager:
            mock_manager.get_config.return_value = None

            response = client.get("/api/config/")

            assert response.status_code == 404

    def test_get_config_success(self):
        """Test getting configuration successfully."""
        with patch("vulkan_agent.routers.config.config_manager") as mock_manager:
            from vulkan_agent.schemas import AgentConfigResponse

            mock_config = AgentConfigResponse(
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini",
                max_tokens=500,
                temperature=0.7,
                api_key_configured=True,
            )
            mock_manager.get_config.return_value = mock_config

            response = client.get("/api/config/")

            assert response.status_code == 200
            data = response.json()
            assert data["provider"] == "openai"
            assert data["model"] == "gpt-4o-mini"
            assert data["api_key_configured"] is True

    def test_update_config_success(self):
        """Test updating configuration successfully."""
        with patch("vulkan_agent.routers.config.config_manager") as mock_manager:
            from vulkan_agent.schemas import AgentConfigResponse

            mock_manager.validate_config.return_value = None  # No exception = valid
            mock_config = AgentConfigResponse(
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini",
                max_tokens=500,
                temperature=0.7,
                api_key_configured=True,
            )
            mock_manager.update_config.return_value = mock_config

            config_data = {
                "provider": "openai",
                "api_key": "sk-test123",
                "model": "gpt-4o-mini",
            }

            response = client.put("/api/config/", json=config_data)

            assert response.status_code == 200
            data = response.json()
            assert data["model"] == "gpt-4o-mini"

    def test_validate_config_endpoint(self):
        """Test configuration validation endpoint."""
        with patch("vulkan_agent.routers.config.config_manager") as mock_manager:
            mock_manager.validate_config.return_value = None  # No exception = valid

            validation_data = {
                "provider": "openai",
                "api_key": "sk-test123",
                "model": "gpt-4o-mini",
            }

            response = client.post("/api/config/validate", json=validation_data)

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["provider"] == "openai"
            assert "successful" in data["message"]

    def test_config_status_endpoint(self):
        """Test configuration status endpoint."""
        with patch("vulkan_agent.routers.config.config_manager") as mock_manager:
            mock_manager.is_configured.return_value = True

            response = client.get("/api/config/status")

            assert response.status_code == 200
            data = response.json()
            assert data["configured"] is True
            assert "ready" in data["message"]


class TestConfigSchemas:
    """Test configuration schemas validation."""

    def test_valid_config_request(self):
        """Test valid configuration request."""
        config = AgentConfigRequest(
            provider=LLMProvider.OPENAI, api_key="sk-test123", model="gpt-4o-mini"
        )

        assert config.provider == LLMProvider.OPENAI
        assert config.api_key == "sk-test123"
        assert config.model == "gpt-4o-mini"
        assert config.max_tokens == 500  # default
        assert config.temperature == 0.7  # default

    def test_invalid_api_key_too_short(self):
        """Test invalid API key (too short)."""
        with pytest.raises(ValueError, match="API key must be at least 5 characters"):
            AgentConfigRequest(
                provider=LLMProvider.OPENAI, api_key="ab", model="gpt-4o-mini"
            )

    def test_agent_config_request_invalid_empty_model(self):
        """Test invalid empty model name (handled by Pydantic)."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            AgentConfigRequest(
                provider=LLMProvider.OPENAI, api_key="valid-key-123", model=""
            )

"""Tests for agent configuration management."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from vulkan_agent.app import app
from vulkan_agent.config import ConfigManager
from vulkan_agent.llm import LLMProvider
from vulkan_agent.schemas import AgentConfigRequest

client = TestClient(app)


class TestConfigManager:
    """Test ConfigManager functionality."""

    def test_init_without_env(self):
        """Test ConfigManager initialization without environment variables."""
        with patch.dict("os.environ", {}, clear=True):
            # Mock database manager to use an in-memory database
            with patch("vulkan_agent.config.get_database_manager") as mock_get_db:
                # Create a real in-memory database for this test
                from vulkan_agent.database import DatabaseManager

                test_db_manager = DatabaseManager(":memory:")
                mock_get_db.return_value = test_db_manager

                manager = ConfigManager()
                assert manager.get_config() is None
                assert not manager.is_configured()

    def test_init_with_env(self):
        """Test ConfigManager initialization with environment variables."""
        env_vars = {
            "DEFAULT_LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-test123",
            "OPENAI_MODEL": "gpt-4o-mini",
            "MAX_TOKENS": "1000",
            "TEMPERATURE": "0.5",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            # Mock database manager to use an in-memory database
            with patch("vulkan_agent.config.get_database_manager") as mock_get_db:
                # Create a real in-memory database for this test
                from vulkan_agent.database import DatabaseManager

                test_db_manager = DatabaseManager(":memory:")
                mock_get_db.return_value = test_db_manager

                manager = ConfigManager()
                config = manager.get_config()

                # Should be None since database config is not set
                assert config is None

    def test_update_config(self):
        """Test updating configuration."""
        manager = ConfigManager()

        config_request = AgentConfigRequest(
            provider=LLMProvider.OPENAI,
            api_key="sk-test123",
            model="gpt-4o-mini",
            max_tokens=800,
            temperature=0.3,
        )

        updated_config = manager.update_config(config_request)

        assert updated_config.provider == LLMProvider.OPENAI
        assert updated_config.model == "gpt-4o-mini"
        assert updated_config.max_tokens == 800
        assert updated_config.temperature == 0.3
        assert updated_config.api_key_configured is True
        assert manager.is_configured()

    def test_get_llm_config(self):
        """Test getting LLM configuration."""
        # Mock database manager to use an in-memory database
        with patch("vulkan_agent.config.get_database_manager") as mock_get_db:
            # Create a real in-memory database for this test
            from vulkan_agent.database import DatabaseManager

            test_db_manager = DatabaseManager(":memory:")
            mock_get_db.return_value = test_db_manager

            manager = ConfigManager()
            assert manager.get_llm_config() is None

        # With configuration
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

    @patch("vulkan_agent.config.LLMClient")
    def test_validate_config_success(self, mock_llm_client):
        """Test successful configuration validation."""
        mock_client_instance = MagicMock()
        mock_client_instance.validate_connection.return_value = True
        mock_llm_client.return_value = mock_client_instance

        manager = ConfigManager()
        # Should not raise exception
        try:
            manager.validate_config(LLMProvider.OPENAI, "sk-test123", "gpt-4o-mini")
        except Exception:
            pytest.fail("validate_config should not raise exception for valid config")

    @patch("vulkan_agent.config.LLMClient")
    def test_validate_config_failure(self, mock_llm_client):
        """Test failed configuration validation."""
        mock_client_instance = MagicMock()
        mock_client_instance.validate_connection.return_value = False
        mock_llm_client.return_value = mock_client_instance

        manager = ConfigManager()
        with pytest.raises(ValueError, match="API key validation failed"):
            manager.validate_config(LLMProvider.OPENAI, "sk-invalid", "gpt-4o-mini")


class TestConfigEndpoints:
    """Test configuration API endpoints."""

    def test_get_config_not_configured(self):
        """Test getting configuration when not configured."""
        with patch("vulkan_agent.routers.config.config_manager") as mock_manager:
            mock_manager.get_config.return_value = None

            response = client.get("/api/config/")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

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

            response = client.post("/api/config/", json=config_data)

            assert response.status_code == 200
            data = response.json()
            assert data["model"] == "gpt-4o-mini"

    def test_update_config_validation_failure(self):
        """Test updating configuration with invalid data."""
        config_data = {
            "provider": "openai",
            "api_key": "invalid-key",  # Invalid format for OpenAI
            "model": "gpt-4o-mini",
        }

        response = client.post("/api/config/", json=config_data)

        # Should be 422 due to Pydantic validation failing first
        assert response.status_code == 422
        assert "OpenAI API keys must start with" in str(response.json())

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

    def test_agent_config_request_valid(self):
        """Test valid AgentConfigRequest."""
        config = AgentConfigRequest(
            provider=LLMProvider.OPENAI, api_key="sk-test123", model="gpt-4o-mini"
        )

        assert config.provider == LLMProvider.OPENAI
        assert config.api_key == "sk-test123"
        assert config.model == "gpt-4o-mini"
        assert config.max_tokens == 500  # default
        assert config.temperature == 0.7  # default

    def test_agent_config_request_invalid_openai_key(self):
        """Test invalid OpenAI API key format."""
        with pytest.raises(ValueError, match='OpenAI API keys must start with "sk-"'):
            AgentConfigRequest(
                provider=LLMProvider.OPENAI, api_key="invalid-key", model="gpt-4o-mini"
            )

    def test_agent_config_request_invalid_anthropic_key(self):
        """Test invalid Anthropic API key format."""
        with pytest.raises(
            ValueError, match='Anthropic API keys must start with "sk-ant-"'
        ):
            AgentConfigRequest(
                provider=LLMProvider.ANTHROPIC,
                api_key="sk-invalid",
                model="claude-3-5-haiku-20241022",
            )

    def test_agent_config_request_invalid_model(self):
        """Test invalid model for provider."""
        with pytest.raises(ValueError, match="Invalid OpenAI model"):
            AgentConfigRequest(
                provider=LLMProvider.OPENAI, api_key="sk-test123", model="invalid-model"
            )

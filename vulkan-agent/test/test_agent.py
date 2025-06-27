"""Tests for agent.py - agent creation and management functionality."""

from unittest.mock import MagicMock, patch

import pytest
from vulkan_agent.agent import (
    create_configured_agent,
    get_global_agent,
    refresh_global_agent,
)
from vulkan_agent.llm import LLMConfig, LLMProvider


class TestAgentCreation:
    """Test agent creation functionality."""

    @patch("vulkan_agent.agent.config_manager")
    @patch("vulkan_agent.agent.create_vulkan_agent")
    @patch("vulkan_agent.agent.create_system_prompt_with_docs")
    @patch("vulkan_agent.agent.get_base_system_prompt")
    def test_create_configured_agent_success(
        self,
        mock_get_base_prompt,
        mock_create_system_prompt,
        mock_create_vulkan_agent,
        mock_config_manager,
    ):
        """Test successful agent creation with configuration."""
        # Setup mocks
        mock_llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            api_key="test-key",
            model="gpt-4o-mini",
        )
        mock_config_manager.get_llm_config.return_value = mock_llm_config
        mock_get_base_prompt.return_value = "Base prompt"
        mock_create_system_prompt.return_value = "Enhanced prompt"
        mock_agent = MagicMock()
        mock_create_vulkan_agent.return_value = mock_agent

        # Call function
        result = create_configured_agent()

        # Verify calls
        mock_config_manager.get_llm_config.assert_called_once()
        mock_get_base_prompt.assert_called_once()
        mock_create_system_prompt.assert_called_once_with("Base prompt")
        mock_create_vulkan_agent.assert_called_once()

        # Verify result
        assert result == mock_agent

    @patch("vulkan_agent.agent.config_manager")
    def test_create_configured_agent_no_config(self, mock_config_manager):
        """Test agent creation fails without configuration."""
        mock_config_manager.get_llm_config.return_value = None

        with pytest.raises(ValueError, match="No agent configuration found"):
            create_configured_agent()

    @patch("vulkan_agent.agent.create_configured_agent")
    def test_get_global_agent_creates_new(self, mock_create_agent):
        """Test getting global agent creates new instance if none exists."""
        # Clear global agent
        import vulkan_agent.agent

        vulkan_agent.agent._global_agent = None

        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        result = get_global_agent()

        mock_create_agent.assert_called_once()
        assert result == mock_agent
        assert vulkan_agent.agent._global_agent == mock_agent

    def test_get_global_agent_returns_existing(self):
        """Test getting global agent returns existing instance."""
        # Set up existing global agent
        import vulkan_agent.agent

        existing_agent = MagicMock()
        vulkan_agent.agent._global_agent = existing_agent

        with patch("vulkan_agent.agent.create_configured_agent") as mock_create:
            result = get_global_agent()

            # Should not create new agent
            mock_create.assert_not_called()
            assert result == existing_agent

    def test_refresh_global_agent(self):
        """Test refreshing global agent clears the instance."""
        # Set up existing global agent
        import vulkan_agent.agent

        vulkan_agent.agent._global_agent = MagicMock()

        refresh_global_agent()

        assert vulkan_agent.agent._global_agent is None

    def teardown_method(self):
        """Clean up after each test."""
        # Clear global agent to avoid test interference
        import vulkan_agent.agent

        vulkan_agent.agent._global_agent = None

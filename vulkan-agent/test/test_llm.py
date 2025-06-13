"""Tests for LLM provider configuration and clients."""

import os
from unittest.mock import MagicMock, patch

from vulkan_agent.llm import LLMClient, LLMConfig, LLMProvider


def test_llm_provider_enum():
    """Test LLM provider enum values."""
    assert LLMProvider.OPENAI == "openai"
    assert LLMProvider.ANTHROPIC == "anthropic"


@patch.dict(
    os.environ,
    {
        "DEFAULT_LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-openai-key",
        "OPENAI_MODEL": "gpt-4",
    },
)
def test_llm_config_from_env_openai():
    """Test creating OpenAI config from environment variables."""
    config = LLMConfig.from_env()

    assert config.provider == LLMProvider.OPENAI
    assert config.api_key == "test-openai-key"
    assert config.model == "gpt-4"


@patch.dict(
    os.environ,
    {
        "DEFAULT_LLM_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "ANTHROPIC_MODEL": "claude-3-sonnet",
    },
)
def test_llm_config_from_env_anthropic():
    """Test creating Anthropic config from environment variables."""
    config = LLMConfig.from_env()

    assert config.provider == LLMProvider.ANTHROPIC
    assert config.api_key == "test-anthropic-key"
    assert config.model == "claude-3-sonnet"


@patch.dict(
    os.environ,
    {
        "OPENAI_API_KEY": "test-key",
        "OPENAI_MODEL": "gpt-3.5-turbo",
    },
)
def test_llm_config_explicit_provider():
    """Test creating config with explicit provider."""
    config = LLMConfig.from_env(LLMProvider.OPENAI)

    assert config.provider == LLMProvider.OPENAI
    assert config.api_key == "test-key"
    assert config.model == "gpt-3.5-turbo"


@patch("vulkan_agent.llm.openai.OpenAI")
def test_llm_client_openai(mock_openai):
    """Test creating OpenAI client."""
    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")

    client = LLMClient(config)

    # Access the client property to trigger creation
    _ = client.client

    mock_openai.assert_called_once_with(api_key="test-key")


@patch("vulkan_agent.llm.anthropic.Anthropic")
def test_llm_client_anthropic(mock_anthropic):
    """Test creating Anthropic client."""
    config = LLMConfig(
        provider=LLMProvider.ANTHROPIC, api_key="test-key", model="claude-3-haiku"
    )

    client = LLMClient(config)

    # Access the client property to trigger creation
    _ = client.client

    mock_anthropic.assert_called_once_with(api_key="test-key")


@patch("vulkan_agent.llm.openai.OpenAI")
def test_validate_connection_openai_success(mock_openai):
    """Test successful OpenAI connection validation."""
    mock_client = MagicMock()
    mock_client.models.list.return_value = []
    mock_openai.return_value = mock_client

    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")

    client = LLMClient(config)
    assert client.validate_connection() is True


@patch("vulkan_agent.llm.openai.OpenAI")
def test_validate_connection_openai_failure(mock_openai):
    """Test failed OpenAI connection validation."""
    mock_client = MagicMock()
    mock_client.models.list.side_effect = Exception("API Error")
    mock_openai.return_value = mock_client

    config = LLMConfig(
        provider=LLMProvider.OPENAI, api_key="invalid-key", model="gpt-4"
    )

    client = LLMClient(config)
    assert client.validate_connection() is False


@patch("vulkan_agent.llm.anthropic.Anthropic")
def test_validate_connection_anthropic_success(mock_anthropic):
    """Test successful Anthropic connection validation."""
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client

    config = LLMConfig(
        provider=LLMProvider.ANTHROPIC, api_key="test-key", model="claude-3-haiku"
    )

    client = LLMClient(config)
    assert client.validate_connection() is True

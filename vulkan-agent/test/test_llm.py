"""Tests for LangChain-based LLM provider configuration and agents."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from vulkan_agent.llm import (
    LLMClient,
    LLMConfig,
    LLMProvider,
    VulkanAgent,
    create_vulkan_agent,
)


def test_llm_provider_enum():
    """Test LLM provider enum values."""
    assert LLMProvider.OPENAI == "openai"
    assert LLMProvider.ANTHROPIC == "anthropic"
    assert LLMProvider.GOOGLE == "google"


@patch("vulkan_agent.llm.ChatOpenAI")
def test_llm_client_openai_creation(mock_chat_openai):
    """Test creating OpenAI LLM client."""
    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")

    client = LLMClient(config)
    # Access the llm property to trigger creation
    _ = client.llm

    mock_chat_openai.assert_called_once_with(
        api_key="test-key",
        model="gpt-4",
        max_tokens=500,
        temperature=0.7,
    )


@patch("vulkan_agent.llm.ChatAnthropic")
def test_llm_client_anthropic_creation(mock_chat_anthropic):
    """Test creating Anthropic LLM client."""
    config = LLMConfig(
        provider=LLMProvider.ANTHROPIC, api_key="test-key", model="claude-3-haiku"
    )

    client = LLMClient(config)
    # Access the llm property to trigger creation
    _ = client.llm

    mock_chat_anthropic.assert_called_once_with(
        api_key="test-key",
        model="claude-3-haiku",
        max_tokens=500,
        temperature=0.7,
    )


@patch("vulkan_agent.llm.ChatGoogleGenerativeAI")
def test_llm_client_google_creation(mock_chat_google):
    """Test creating Google LLM client."""
    config = LLMConfig(
        provider=LLMProvider.GOOGLE, api_key="test-key", model="gemini-1.5-pro"
    )

    client = LLMClient(config)
    # Access the llm property to trigger creation
    _ = client.llm

    mock_chat_google.assert_called_once_with(
        api_key="test-key",
        model="gemini-1.5-pro",
        max_tokens=500,
        temperature=0.7,
    )


@patch("vulkan_agent.llm.ChatOpenAI")
def test_llm_client_validate_connection_success(mock_chat_openai):
    """Test successful connection validation."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock()
    mock_chat_openai.return_value = mock_llm

    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")
    client = LLMClient(config)

    assert client.validate_connection() is True


@patch("vulkan_agent.llm.ChatOpenAI")
def test_llm_client_validate_connection_failure(mock_chat_openai):
    """Test failed connection validation."""
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = Exception("API Error")
    mock_chat_openai.return_value = mock_llm

    config = LLMConfig(
        provider=LLMProvider.OPENAI, api_key="invalid-key", model="gpt-4"
    )
    client = LLMClient(config)

    assert client.validate_connection() is False


def test_vulkan_agent_session_management():
    """Test VulkanAgent session management functionality."""
    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")

    with patch("vulkan_agent.llm.ChatOpenAI"):
        llm_client = LLMClient(config)
        agent = VulkanAgent(llm_client)

        # Test setting session
        agent.set_session("test-session-123")
        assert agent._current_session_id == "test-session-123"

        # Test clearing session (no errors should occur)
        agent.clear_memory("test-session-123")


def test_vulkan_agent_creation():
    """Test VulkanAgent creation."""
    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")

    with patch("vulkan_agent.llm.ChatOpenAI"):
        llm_client = LLMClient(config)
        agent = VulkanAgent(llm_client)

        assert agent.llm_client == llm_client
        assert agent.tools == []
        assert "Vulkan platform" in agent.system_prompt


@patch("vulkan_agent.llm.ChatOpenAI")
@pytest.mark.asyncio
async def test_vulkan_agent_chat_without_tools(mock_chat_openai):
    """Test VulkanAgent chat without tools."""
    mock_response = MagicMock()
    mock_response.content = "I can help with Vulkan!"

    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    mock_chat_openai.return_value = mock_llm

    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")
    llm_client = LLMClient(config)
    agent = VulkanAgent(llm_client)

    response = await agent.chat("Help me with policies")
    assert response == "I can help with Vulkan!"


def test_vulkan_agent_add_tool():
    """Test adding tools to VulkanAgent."""
    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")

    with patch("vulkan_agent.llm.ChatOpenAI"):
        llm_client = LLMClient(config)
        agent = VulkanAgent(llm_client)

        # Mock tool
        mock_tool = MagicMock()
        agent.add_tool(mock_tool)

        assert len(agent.tools) == 1
        assert agent.tools[0] == mock_tool


def test_vulkan_agent_set_system_prompt():
    """Test setting system prompt for VulkanAgent."""
    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")

    with patch("vulkan_agent.llm.ChatOpenAI"):
        llm_client = LLMClient(config)
        agent = VulkanAgent(llm_client)

        new_prompt = "You are a specialized Vulkan assistant."
        agent.set_system_prompt(new_prompt)

        assert agent.system_prompt == new_prompt


def test_vulkan_agent_clear_memory():
    """Test clearing memory for VulkanAgent."""
    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")

    with patch("vulkan_agent.llm.ChatOpenAI"):
        mock_manager_instance = MagicMock()

        llm_client = LLMClient(config)
        agent = VulkanAgent(llm_client)

        # Mock the session_manager property
        agent.session_manager = mock_manager_instance

        agent.clear_memory("test-session")
        mock_manager_instance.clear_session_messages.assert_called_once_with(
            "test-session"
        )


def test_create_vulkan_agent_factory():
    """Test create_vulkan_agent factory function."""
    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")

    with patch("vulkan_agent.llm.ChatOpenAI"):
        agent = create_vulkan_agent(config)

        assert isinstance(agent, VulkanAgent)
        assert agent.llm_client.config == config


def test_create_vulkan_agent_with_tools():
    """Test create_vulkan_agent factory function with tools."""
    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")
    mock_tools = [MagicMock(), MagicMock()]

    with patch("vulkan_agent.llm.ChatOpenAI"):
        agent = create_vulkan_agent(config, tools=mock_tools)

        assert isinstance(agent, VulkanAgent)
        assert len(agent.tools) == 2


def test_llm_config_validation():
    """Test LLMConfig field validation."""
    # Test valid config
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key="test-key",
        model="gpt-4",
        max_tokens=1000,
        temperature=0.5,
    )
    assert config.max_tokens == 1000
    assert config.temperature == 0.5


def test_llm_config_unsupported_provider():
    """Test handling of unsupported provider via direct config creation."""
    # Test that LLMProvider enum rejects invalid values during construction
    with pytest.raises(ValueError, match="not a valid LLMProvider"):
        LLMProvider("unsupported")


def test_llm_client_unsupported_provider():
    """Test LLMClient with unsupported provider."""
    # This would require creating an invalid enum value manually
    # For now, we'll test the error handling in the provider creation
    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")
    config.provider = "invalid"  # Manually set invalid provider

    client = LLMClient(config)

    with pytest.raises(ValueError, match="Unsupported provider"):
        _ = client.llm


def test_vulkan_agent_get_status():
    """Test VulkanAgent get_status method."""
    config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test-key", model="gpt-4")
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"

    with patch("vulkan_agent.llm.ChatOpenAI"):
        llm_client = LLMClient(config)
        agent = VulkanAgent(llm_client, tools=[mock_tool])

        # Set a session
        agent.set_session("test-session-123")

        status = agent.get_status()

        assert status["provider"] == "openai"
        assert status["model"] == "gpt-4"
        assert status["tools_count"] == 1
        assert status["available_tools"] == ["test_tool"]
        assert status["current_session"] == "test-session-123"

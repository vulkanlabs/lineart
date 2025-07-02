"""Essential integration test - Core functionality only."""

from vulkan_agent.config import ConfigManager
from vulkan_agent.llm import LLMProvider, create_vulkan_agent
from vulkan_agent.schemas import AgentConfigRequest


def test_core_integration():
    """Test that core components work together."""
    # Test configuration
    manager = ConfigManager()
    config_request = AgentConfigRequest(
        provider=LLMProvider.OPENAI, api_key="sk-test123", model="gpt-4o-mini"
    )

    # Update config
    updated_config = manager.update_config(config_request)
    assert updated_config.api_key_configured is True
    assert manager.is_configured()

    # Get LLM config
    llm_config = manager.get_llm_config()
    assert llm_config is not None

    # Create agent
    agent = create_vulkan_agent(llm_config, "Test prompt")
    assert agent is not None
    assert agent.system_prompt == "Test prompt"

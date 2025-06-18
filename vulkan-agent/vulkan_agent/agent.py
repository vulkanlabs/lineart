"""
Vulkan Chat Agent module for creating and managing the AI agent.

This module handles:
- Agent creation and configuration with tools
- Tool loading and management
- Agent status checking
- Global agent instance management
- Documentation context integration
"""

from typing import List, Optional, Tuple

from langchain_core.tools import BaseTool

from .config import config_manager
from .knowledge_base import create_system_prompt_with_docs
from .llm import VulkanAgent, create_vulkan_agent


class AgentToolsManager:
    """Manages tools for the Vulkan AI Agent."""

    def __init__(self):
        self._tools_cache: Optional[List[BaseTool]] = None
        self._last_config_hash: Optional[str] = None

    def get_available_tools(self) -> Tuple[List[BaseTool], dict]:
        """
        Get all available tools for the agent.

        Returns:
            Tuple of (tools_list, capabilities_info)
        """
        tools = []
        capabilities = {
            "documentation_available": True,  # Always available with new approach
            "tools_count": 0,
            "available_tools": [],
        }

        # Future: Add tools here as they are developed
        # For example:
        # - Policy management tools
        # - Data source management tools
        # - Workflow management tools
        # - File upload/processing tools

        # Example of how to add tools:
        # policy_tools = self._get_policy_tools()
        # tools.extend(policy_tools)

        # data_source_tools = self._get_data_source_tools()
        # tools.extend(data_source_tools)

        capabilities["tools_count"] = len(tools)
        capabilities["available_tools"] = [tool.name for tool in tools]

        return tools, capabilities

    def _get_policy_tools(self) -> List[BaseTool]:
        """Get policy management tools (to be implemented)."""
        # Placeholder for future policy management tools
        return []

    def _get_data_source_tools(self) -> List[BaseTool]:
        """Get data source management tools (to be implemented)."""
        # Placeholder for future data source management tools
        return []

    def clear_cache(self) -> None:
        """Clear the tools cache."""
        self._tools_cache = None
        self._last_config_hash = None


def create_configured_agent() -> VulkanAgent:
    """Create and configure a Vulkan agent with available tools and documentation context.

    Raises:
        ValueError: If no configuration is found in the database
    """
    # Get LLM configuration from database
    llm_config = config_manager.get_llm_config()

    # Require explicit configuration via API
    if llm_config is None:
        raise ValueError(
            "No agent configuration found. Please configure the agent using the /api/config endpoint."
        )

    # Get available tools
    tools_manager = AgentToolsManager()
    tools, capabilities = tools_manager.get_available_tools()

    # Create agent with tools
    agent = create_vulkan_agent(llm_config, tools)

    # Set system prompt with embedded documentation
    base_prompt = """You are a helpful AI assistant for the Vulkan platform. 
    You help users manage policies, data sources, and other resources.
    
    Always be helpful, accurate, and ask clarifying questions when needed.
    If you're unsure about something, refer to the documentation provided in your context.
    """

    # Enhanced prompt with documentation context
    enhanced_prompt = create_system_prompt_with_docs(base_prompt)
    agent.set_system_prompt(enhanced_prompt)

    return agent


def get_agent_status() -> dict:
    """Get the status of the agent and its components."""
    tools_manager = AgentToolsManager()
    tools, capabilities = tools_manager.get_available_tools()

    return {
        "agent_configured": config_manager.is_configured(),
        **capabilities,
    }


# Global agent instance for reuse
_global_agent: Optional[VulkanAgent] = None


def get_global_agent() -> VulkanAgent:
    """Get the global agent instance, creating it if needed."""
    global _global_agent
    if _global_agent is None:
        _global_agent = create_configured_agent()
    return _global_agent


def refresh_global_agent() -> None:
    """Refresh the global agent (useful when config or documentation changes)."""
    global _global_agent
    _global_agent = None

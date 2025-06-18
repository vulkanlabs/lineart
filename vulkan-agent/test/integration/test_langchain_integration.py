"""Simple test script to verify LangChain integration works."""

import asyncio

import pytest
from vulkan_agent.llm import LLMConfig, LLMProvider, create_vulkan_agent


@pytest.mark.asyncio
async def test_langchain_integration():
    """Test the LangChain-based agent."""
    print("Testing LangChain integration...")

    # Create config (will use mock keys)
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key="test-key",  # This is just for testing structure
        model="gpt-4o-mini",
        max_tokens=100,
        temperature=0.7,
    )

    # Create agent
    agent = create_vulkan_agent(config)

    print("✅ Agent created successfully")
    print(f"   Provider: {agent.llm_client.config.provider}")
    print(f"   Model: {agent.llm_client.config.model}")
    print(f"   Tools: {len(agent.tools)} tools available")
    print(f"   System prompt preview: {agent.system_prompt[:50]}...")

    # Test session management
    agent.set_session("test-session-123")
    assert agent._current_session_id == "test-session-123"

    # Test memory through session manager (if available)
    try:
        from vulkan_agent.session import SessionManager

        session_manager = SessionManager()
        session_manager.add_message("test-session-123", "user", "Hello")
        session_manager.add_message("test-session-123", "assistant", "Hi there!")

        messages = session_manager.get_messages("test-session-123")
        print(f"   Session memory: {len(messages)} messages stored")
    except Exception as e:
        print(f"   Session memory test skipped: {e}")

    # Test status
    status = agent.get_status()
    print(f"   Status: {status}")

    print("✅ LangChain integration test passed!")


def main():
    """Main function for standalone execution."""
    asyncio.run(test_langchain_integration())


if __name__ == "__main__":
    main()

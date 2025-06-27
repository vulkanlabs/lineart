"""LangChain-based LLM provider configuration and agents for vulkan-agent."""

from enum import Enum
from functools import cached_property
from typing import List, Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .models import MessageRole
from .session import get_session_manager

MAX_ALLOWED_TOKENS = 1000000  # Maximum allowed tokens for LLMs, adjust as needed


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class LLMConfig(BaseModel):
    """Configuration for LLM providers using LangChain."""

    provider: LLMProvider
    api_key: str
    model: str
    max_tokens: int = Field(default=500, ge=1, le=MAX_ALLOWED_TOKENS)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class LLMClient:
    """Simple LangChain-based LLM client for provider management."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._llm: Optional[BaseChatModel] = None

    @property
    def llm(self) -> BaseChatModel:
        """Get the LangChain LLM instance."""
        if self._llm is None:
            if self.config.provider == LLMProvider.OPENAI:
                self._llm = ChatOpenAI(
                    api_key=self.config.api_key,
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                )
            elif self.config.provider == LLMProvider.ANTHROPIC:
                self._llm = ChatAnthropic(
                    api_key=self.config.api_key,
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                )
            elif self.config.provider == LLMProvider.GOOGLE:
                self._llm = ChatGoogleGenerativeAI(
                    api_key=self.config.api_key,
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                )
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
        return self._llm

    def validate_connection(self) -> bool:
        """Validate that the API key and connection work."""
        try:
            # Test with a simple message
            test_messages = [HumanMessage(content="Hello")]
            self.llm.invoke(test_messages)
            return True
        except Exception:
            return False


class VulkanAgent:
    """Complete Vulkan AI Agent with LLM, tools, and session-based conversation management."""

    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str,
        tools: Optional[List[BaseTool]] = None,
    ):
        """Initialize the Vulkan Agent.

        Args:
            llm_client: The LLM client to use for responses
            system_prompt: The system prompt for the agent
            tools: Optional list of tools for the agent to use
        """
        self.llm_client = llm_client
        self.tools = tools or []
        self._agent_executor: Optional[AgentExecutor] = None
        self._current_session_id: Optional[str] = None

        # Store the system prompt
        self._system_prompt = system_prompt

    @cached_property
    def session_manager(self):
        """Get session manager instance (cached import)."""
        return get_session_manager()

    @property
    def system_prompt(self) -> str:
        """Get the current system prompt."""
        return self._system_prompt

    @property
    def agent_executor(self) -> AgentExecutor:
        """Get the agent executor, creating it if needed."""
        if self._agent_executor is None:
            if not self.tools:
                raise ValueError("Cannot create agent executor without tools")

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self.system_prompt),
                    MessagesPlaceholder("chat_history", optional=True),
                    ("human", "{input}"),
                    MessagesPlaceholder("agent_scratchpad"),
                ]
            )

            # Create agent
            agent = create_tool_calling_agent(self.llm_client.llm, self.tools, prompt)

            # Create executor
            self._agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5,
            )
        return self._agent_executor

    async def chat(self, user_input: str, session_id: Optional[str] = None) -> str:
        """Main chat interface for the agent.

        Args:
            user_input: The user's message
            session_id: Optional session ID for conversation memory
        """
        # Use provided session_id or current session
        active_session = session_id or self._current_session_id

        if self.tools:
            # Use agent with tools
            chat_history = self._get_session_history(active_session)
            result = await self.agent_executor.ainvoke(
                {"input": user_input, "chat_history": chat_history}
            )
            response = result["output"]
        else:
            # Use simple LLM conversation
            response = await self._generate_simple_response(user_input, active_session)

        # Save conversation to session
        self._save_to_session(active_session, user_input, response)
        return response

    async def _generate_simple_response(
        self, user_input: str, session_id: Optional[str]
    ) -> str:
        """Generate a response using simple LLM conversation with session memory."""
        # Build message history
        messages = [SystemMessage(content=self.system_prompt)]

        # Add conversation history from session
        if session_id:
            session_messages = self._get_session_history(session_id)
            messages.extend(session_messages)

        # Add current user input
        messages.append(HumanMessage(content=user_input))

        # Generate response
        response = await self.llm_client.llm.ainvoke(messages)
        return response.content

    def set_session(self, session_id: str):
        """Set the current session for conversation memory."""
        self._current_session_id = session_id

    def set_system_prompt(self, prompt: str) -> None:
        """Update the system prompt.

        Args:
            prompt: New system prompt
        """
        self._system_prompt = prompt
        # Reset agent executor to pick up new prompt
        self._agent_executor = None

    def add_tool(self, tool: BaseTool) -> None:
        """Add a tool to the agent."""
        self.tools.append(tool)
        # Reset agent executor to pick up new tool
        self._agent_executor = None

    def clear_memory(self, session_id: Optional[str] = None) -> None:
        """Clear conversation memory for a session."""
        if session_id:
            self.session_manager.clear_session_messages(session_id)

    def get_status(self) -> dict:
        """Get agent status information."""
        return {
            "provider": self.llm_client.config.provider.value,
            "model": self.llm_client.config.model,
            "tools_count": len(self.tools),
            "available_tools": [tool.name for tool in self.tools],
            "current_session": self._current_session_id,
        }

    def _get_session_history(self, session_id: Optional[str]) -> List:
        """Get conversation history for a session."""
        if not session_id:
            return []
        return self.session_manager.get_messages_as_langchain(session_id)

    def _save_to_session(
        self, session_id: Optional[str], user_message: str, ai_response: str
    ):
        """Save conversation to session."""
        if session_id:
            self.session_manager.add_message(session_id, MessageRole.USER, user_message)
            self.session_manager.add_message(
                session_id, MessageRole.ASSISTANT, ai_response
            )


# Factory function for easy agent creation
def create_vulkan_agent(
    config: LLMConfig, system_prompt: str, tools: Optional[List[BaseTool]] = None
) -> VulkanAgent:
    """Create a configured Vulkan agent.

    Args:
        config: LLM configuration
        system_prompt: System prompt for the agent
        tools: Optional list of tools for the agent
    """
    llm_client = LLMClient(config)
    return VulkanAgent(llm_client, system_prompt, tools)

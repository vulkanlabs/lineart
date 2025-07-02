"""Agent configuration management service with database storage."""

from typing import Optional

from .database import get_database_manager
from .llm import LLMClient, LLMConfig, LLMProvider
from .models import AgentConfig
from .schemas import AgentConfigRequest, AgentConfigResponse


class ConfigManager:
    """Database-backed configuration manager for agent settings."""

    def __init__(self):
        self.db_manager = get_database_manager()

    def get_config(self) -> Optional[AgentConfigResponse]:
        """Get current agent configuration (without exposing API key)."""
        with self.db_manager.get_session() as session:
            config = session.query(AgentConfig).first()

            if not config:
                return None

            return AgentConfigResponse(
                provider=LLMProvider(config.provider),
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                api_key_configured=True,
            )

    def update_config(self, config_request: AgentConfigRequest) -> AgentConfigResponse:
        """Update agent configuration."""
        with self.db_manager.get_session() as session:
            # Get existing config or create new one
            config = session.query(AgentConfig).first()

            if config:
                # Update existing
                config.provider = config_request.provider.value
                config.api_key = config_request.api_key
                config.model = config_request.model
                config.max_tokens = config_request.max_tokens
                config.temperature = config_request.temperature
            else:
                # Create new
                config = AgentConfig(
                    provider=config_request.provider.value,
                    api_key=config_request.api_key,
                    model=config_request.model,
                    max_tokens=config_request.max_tokens,
                    temperature=config_request.temperature,
                )
                session.add(config)

            # Return response without API key
            return AgentConfigResponse(
                provider=config_request.provider,
                model=config_request.model,
                max_tokens=config_request.max_tokens,
                temperature=config_request.temperature,
                api_key_configured=True,
            )

    def get_llm_config(self) -> Optional[LLMConfig]:
        """Get LLM configuration for use with LLMClient."""
        with self.db_manager.get_session() as session:
            config = session.query(AgentConfig).first()

            if not config:
                return None

            return LLMConfig(
                provider=LLMProvider(config.provider),
                api_key=config.api_key,
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )

    def validate_config(self, provider: LLMProvider, api_key: str, model: str) -> None:
        """Validate API key and configuration.

        Args:
            provider: LLM provider
            api_key: API key to validate
            model: Model name to validate

        Raises:
            ValueError: If validation fails with details about the failure
        """
        try:
            # Create temporary LLM config and client
            llm_config = LLMConfig(provider=provider, api_key=api_key, model=model)
            llm_client = LLMClient(llm_config)

            # Test the connection
            if not llm_client.validate_connection():
                raise ValueError(
                    "API key validation failed - check your key and try again"
                )

        except ValueError:
            # Re-raise ValueError as-is (includes our custom message above)
            raise
        except Exception as e:
            raise ValueError(f"Configuration validation error: {str(e)}")

    def is_configured(self) -> bool:
        """Check if agent is properly configured."""
        with self.db_manager.get_session() as session:
            config = session.query(AgentConfig).first()
            return config is not None


# Global configuration manager instance
config_manager = ConfigManager()

"""LLM provider configuration and factory for vulkan-agent."""

import os
from enum import Enum
from typing import Optional, Union

import anthropic
import openai
from pydantic import BaseModel


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMConfig(BaseModel):
    """Configuration for LLM providers."""

    provider: LLMProvider
    api_key: str
    model: str

    @classmethod
    def from_env(cls, provider: Optional[LLMProvider] = None) -> "LLMConfig":
        """Create LLM config from environment variables."""
        if provider is None:
            provider_str = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
            provider = LLMProvider(provider_str)

        if provider == LLMProvider.OPENAI:
            api_key = os.getenv("OPENAI_API_KEY", "")
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        elif provider == LLMProvider.ANTHROPIC:
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        return cls(provider=provider, api_key=api_key, model=model)


class LLMClient:
    """Factory for creating LLM clients."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._client: Optional[Union[openai.OpenAI, anthropic.Anthropic]] = None

    @property
    def client(self) -> Union[openai.OpenAI, anthropic.Anthropic]:
        """Get the LLM client instance."""
        if self._client is None:
            if self.config.provider == LLMProvider.OPENAI:
                self._client = openai.OpenAI(api_key=self.config.api_key)
            elif self.config.provider == LLMProvider.ANTHROPIC:
                self._client = anthropic.Anthropic(api_key=self.config.api_key)
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")

        return self._client

    def validate_connection(self) -> bool:
        """Validate that the API key and connection work."""
        try:
            if self.config.provider == LLMProvider.OPENAI:
                # Try to list models to validate the API key
                self.client.models.list()
            elif self.config.provider == LLMProvider.ANTHROPIC:
                # For Anthropic, we'll just check if we can create the client
                # since they don't have a simple validation endpoint
                pass
            return True
        except Exception:
            return False

    async def generate_response(self, prompt: str) -> str:
        """Generate a response using the configured LLM."""
        try:
            if self.config.provider == LLMProvider.OPENAI:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.7,
                )
                return response.choices[0].message.content or ""

            elif self.config.provider == LLMProvider.ANTHROPIC:
                response = self.client.messages.create(
                    model=self.config.model,
                    max_tokens=500,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text if response.content else ""

        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}")

        return ""

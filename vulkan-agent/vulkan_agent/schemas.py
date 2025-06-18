"""Pydantic schemas for vulkan-agent requests and responses."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .llm import LLMProvider


class AgentConfigRequest(BaseModel):
    """Request schema for updating agent configuration."""

    provider: LLMProvider = Field(..., description="LLM provider to use")
    api_key: str = Field(..., min_length=1, description="API key for the LLM provider")
    model: str = Field(..., min_length=1, description="Model name to use")
    max_tokens: Optional[int] = Field(
        500, ge=1, le=4000, description="Maximum tokens per response"
    )
    temperature: Optional[float] = Field(
        0.7, ge=0.0, le=2.0, description="Response creativity level"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v, info):
        """Basic API key format validation."""
        if "provider" in info.data:
            provider = info.data["provider"]
            if provider == LLMProvider.OPENAI and not v.startswith("sk-"):
                raise ValueError('OpenAI API keys must start with "sk-"')
            elif provider == LLMProvider.ANTHROPIC and not v.startswith("sk-ant-"):
                raise ValueError('Anthropic API keys must start with "sk-ant-"')
        return v

    @field_validator("model")
    @classmethod
    def validate_model(cls, v, info):
        """Basic model name validation."""
        if "provider" in info.data:
            provider = info.data["provider"]
            if provider == LLMProvider.OPENAI:
                valid_models = ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]
                if v not in valid_models:
                    raise ValueError(f"Invalid OpenAI model. Supported: {valid_models}")
            elif provider == LLMProvider.ANTHROPIC:
                valid_models = [
                    "claude-3-5-haiku-20241022",
                    "claude-3-5-sonnet-20241022",
                    "claude-3-opus-20240229",
                ]
                if v not in valid_models:
                    raise ValueError(
                        f"Invalid Anthropic model. Supported: {valid_models}"
                    )
        return v


class AgentConfigResponse(BaseModel):
    """Response schema for agent configuration."""

    provider: LLMProvider
    model: str
    max_tokens: int
    temperature: float
    api_key_configured: bool = Field(
        description="Whether an API key is configured (without exposing the key)"
    )


class AgentConfigValidationRequest(BaseModel):
    """Request schema for validating API key configuration."""

    provider: LLMProvider
    api_key: str
    model: Optional[str] = None


class AgentConfigValidationResponse(BaseModel):
    """Response schema for API key validation."""

    valid: bool
    message: str
    provider: LLMProvider


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str
    detail: Optional[str] = None


class ChatRequest(BaseModel):
    """Request schema for chat messages."""

    message: str = Field(
        ..., min_length=1, description="User message to send to the agent"
    )
    session_id: Optional[str] = Field(
        None, description="Optional session ID for conversation memory"
    )


class ChatResponse(BaseModel):
    """Response schema for chat messages."""

    response: str = Field(..., description="Agent's response to the user message")
    session_id: Optional[str] = Field(
        None, description="Session ID used for this conversation"
    )
    tools_used: bool = Field(
        default=False,
        description="Whether any tools were used to generate the response",
    )

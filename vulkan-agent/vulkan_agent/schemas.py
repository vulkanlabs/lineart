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
        500, ge=1, le=100000, description="Maximum tokens per response"
    )
    temperature: Optional[float] = Field(
        0.7, ge=0.0, le=2.0, description="Response creativity level"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        """Basic API key validation - ensure it's meaningful."""
        stripped = v.strip()
        if len(stripped) < 5:
            raise ValueError("API key must be at least 5 characters long")
        return stripped


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

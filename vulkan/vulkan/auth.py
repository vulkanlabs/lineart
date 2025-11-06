"""
Authentication configuration schemas for Data Sources.

This module defines the authentication types supported by the system.
Supports Basic and Bearer/OAuth authentication methods.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class AuthMethod(str, Enum):
    BASIC = "basic"
    BEARER = "bearer"


class GrantType(str, Enum):
    CLIENT_CREDENTIALS = "client_credentials"
    PASSWORD = "password"
    IMPLICIT = "implicit"


class AuthConfig(BaseModel):
    """
    Unified authentication configuration for DataSources.

    The auth config defines HOW to authenticate (method, endpoints, etc).
    The actual credentials (CLIENT_ID, CLIENT_SECRET) are configured separately
    via environment variables and stored securely in the database.

    Configuration Flow:
        1. User creates DataSource with AuthConfig (this object)
        2. User separately sets CLIENT_ID and CLIENT_SECRET as env vars
        3. Backend stores credentials securely (CLIENT_SECRET encrypted)
        4. At runtime, credentials are retrieved and used with this auth config

    """

    method: AuthMethod = Field(
        ...,
        description="Authentication method: 'basic' or 'bearer'",
    )

    # Required for Bearer/OAuth
    token_url: str | None = Field(
        None,
        description="OAuth token endpoint URL (required for bearer auth)",
        examples=["https://api.example.com/oauth/token"],
    )

    grant_type: GrantType | None = Field(
        None,
        description="OAuth grant type (required for bearer auth)",
    )

    scope: str | None = Field(
        None,
        description="OAuth scope - space-separated list (optional)",
        examples=["api.read api.write", "https://api.example.com/.default"],
    )

    @field_validator("token_url", "grant_type")
    @classmethod
    def validate_bearer_fields(cls, v, info):
        """Validates that required fields are present for Bearer authentication."""
        if info.data.get("method") == AuthMethod.BEARER:
            if v is None:
                field_name = info.field_name
                raise ValueError(
                    f"{field_name} is required when using Bearer authentication"
                )
        return v

    @field_validator("token_url")
    @classmethod
    def validate_token_url_format(cls, v):
        """Validates token_url format if provided."""
        if v is not None:
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError("token_url must start with 'http://' or 'https://'")
        return v

    def requires_token_exchange(self) -> bool:
        """
        Returns True if this auth config requires token exchange.

        Token exchange is needed for Bearer/OAuth authentication.
        """
        return self.method == AuthMethod.BEARER

    class Config:
        """Pydantic config."""

        use_enum_values = False

from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel, field_validator

from vulkan.auth import AuthConfig
from vulkan.connections import HTTPConfig
from vulkan.credentials import validate_no_reserved_credentials_in_templates
from vulkan.node_config import (
    extract_env_vars,
    extract_env_vars_from_string,
    extract_runtime_params,
    extract_runtime_params_from_string,
)


class DataSourceType(Enum):
    HTTP = "http"
    LOCAL_FILE = "local_file"
    REGISTERED_FILE = "registered_file"


class DataSourceStatus(Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class SourceSpecBase(ABC):
    @abstractmethod
    def extract_env_vars(self) -> list[str]:
        pass

    @abstractmethod
    def extract_runtime_params(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def source_type(self) -> DataSourceType:
        pass


class RegisteredFileSource(BaseModel, SourceSpecBase):
    file_id: str
    path: str | None = None

    def extract_env_vars(self) -> list[str]:
        return []

    def extract_runtime_params(self) -> list[str]:
        return []

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.REGISTERED_FILE


class LocalFileSource(BaseModel):
    path: str

    def extract_env_vars(self) -> list[str]:
        return []

    def extract_runtime_params(self) -> list[str]:
        return []

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.LOCAL_FILE


class HTTPSource(HTTPConfig, SourceSpecBase):
    """HTTP data source configuration with optional authentication."""

    auth: AuthConfig | None = None

    def extract_env_vars(self) -> list[str]:
        """
        Extracts environment variables from URL, headers, params, and body.

        Note: Does NOT include CLIENT_ID/CLIENT_SECRET.
        Those are reserved for authentication and managed separately.
        """
        env_vars = extract_env_vars_from_string(self.url)
        for spec in [self.headers, self.params, self.body]:
            if spec is not None:
                env_vars += extract_env_vars(spec)
        return env_vars

    def extract_runtime_params(self) -> list[str]:
        """Extracts runtime parameters from URL, headers, params, and body."""
        params = extract_runtime_params_from_string(self.url)
        for spec in [self.headers, self.params, self.body]:
            if spec is not None:
                params += extract_runtime_params(spec)
        return params

    @field_validator("auth", mode="after")
    @classmethod
    def validate_auth_secrets_not_in_templates(cls, v, info):
        """
        Validates that reserved credential names are not used in templates.

        Uses shared validation function to ensure consistency across the codebase.
        """
        if v is None:
            return v

        data = info.data

        env_vars = []
        if "url" in data:
            env_vars += extract_env_vars_from_string(data["url"])
        for field in ["headers", "params", "body"]:
            if field in data and data[field] is not None:
                env_vars += extract_env_vars(data[field])

        validate_no_reserved_credentials_in_templates(
            env_vars, error_context="templates"
        )

        return v

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.HTTP

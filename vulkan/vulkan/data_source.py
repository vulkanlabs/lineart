from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel, field_validator

from vulkan.auth import Auth
from vulkan.connections import HTTPConfig
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

    auth: Auth | None = None

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
        Validates that auth secrets (CLIENT_ID, CLIENT_SECRET) are not
        used in templates.

        These are reserved names for authentication credentials
        """
        if v is None:
            return v

        data = info.data
        reserved_names = {"CLIENT_ID", "CLIENT_SECRET"}

        env_vars = []
        if "url" in data:
            env_vars += extract_env_vars_from_string(data["url"])
        for field in ["headers", "params", "body"]:
            if field in data and data[field] is not None:
                env_vars += extract_env_vars(data[field])

        conflicts = reserved_names.intersection(env_vars)
        if conflicts:
            raise ValueError(
                f"Auth credentials cannot be used in templates: {', '.join(conflicts)}. "
                f"CLIENT_ID and CLIENT_SECRET are reserved for authentication only."
            )

        return v

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.HTTP

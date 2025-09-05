"""Configuration classes for vulkan-engine.

This module defines all configuration dataclasses that vulkan-server
and other implementations can use and extend.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class DatabaseConfig:
    """Configuration for the main application database."""

    user: str
    password: str
    host: str
    port: str
    database: str

    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class DagsterDatabaseConfig:
    """Configuration for the Dagster database."""

    user: str
    password: str
    host: str
    port: str
    database: str

    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string for Dagster."""
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class DagsterServiceConfig:
    """Configuration for connecting to Dagster service."""

    host: str
    port: str
    server_port: str

    @property
    def base_url(self) -> str:
        """Get base URL for Dagster service."""
        return f"http://{self.host}:{self.port}"

    @property
    def server_url(self) -> str:
        """Get server URL for Dagster service."""
        return f"http://{self.host}:{self.server_port}"


@dataclass
class ExternalServiceConfig:
    """Configuration for external services."""

    resolution_service_url: str | None = None
    beam_launcher_url: str | None = None


@dataclass
class AppConfig:
    """Configuration for the application server."""

    host: str
    port: str

    @property
    def server_url(self) -> str:
        """Get the server URL."""
        return f"http://{self.host}:{self.port}"


@dataclass
class WorkerDatabaseConfig:
    """Unified database configuration for workflow engines."""

    enabled: bool
    user: str | None = None
    password: str | None = None
    host: str | None = None
    port: str | None = None
    database: str | None = None

    @property
    def connection_string(self) -> str | None:
        """Get PostgreSQL connection string if database is enabled and configured."""
        if not self.enabled or not all(
            [self.user, self.password, self.host, self.port, self.database]
        ):
            return None
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class WorkerServiceConfig:
    """Unified service configuration for workflow engines."""

    worker_type: Literal["dagster", "hatchet"]
    host: str
    port: str
    server_port: str | None = None  # Dagster-specific

    # Hatchet-specific fields
    home_path: str | None = None
    scripts_path: str | None = None
    workspaces_path: str | None = None

    @property
    def base_url(self) -> str:
        """Get base URL for the worker service."""
        return f"http://{self.host}:{self.port}"

    @property
    def server_url(self) -> str:
        """Get server URL for the worker service."""
        if self.worker_type == "dagster" and self.server_port:
            return f"http://{self.host}:{self.server_port}"
        return f"http://{self.host}:{self.port}"


@dataclass
class LoggingConfig:
    """
    Configuration for logging services.

    Enables optional cloud logging integration. When gcp_project_id is provided,
    logs will be sent to Google Cloud Logging if the GCP dependencies are available.
    """

    gcp_project_id: str | None = None
    """GCP project ID for cloud logging. If None, only local logging is used."""


@dataclass
class VulkanEngineConfig:
    """Complete configuration for vulkan-engine."""

    app: AppConfig
    database: DatabaseConfig
    external_services: ExternalServiceConfig
    logging: LoggingConfig

    # Unified worker configuration
    worker_database: WorkerDatabaseConfig
    worker_service: WorkerServiceConfig

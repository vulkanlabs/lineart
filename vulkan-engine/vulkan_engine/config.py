"""Configuration classes for vulkan-engine.

This module defines all configuration dataclasses that vulkan-server
and other implementations can use and extend.
"""

from dataclasses import dataclass
from typing import Literal, Union


@dataclass
class DagsterConfig:
    """Configuration specific to Dagster backend."""

    worker_url: str


@dataclass
class HatchetConfig:
    """Configuration specific to Hatchet backend."""

    hatchet_token: str


@dataclass
class WorkerServiceConfig:
    """Unified service configuration for workflow engines."""

    worker_type: Literal["dagster", "hatchet"]
    server_url: str
    service_config: Union[DagsterConfig, HatchetConfig]

    def __post_init__(self):
        """Validate that the config matches the worker type."""
        if self.worker_type == "dagster" and not isinstance(
            self.service_config, DagsterConfig
        ):
            raise ValueError(
                "service_config must be DagsterConfig for dagster worker type"
            )
        elif self.worker_type == "hatchet" and not isinstance(
            self.service_config, HatchetConfig
        ):
            raise ValueError(
                "service_config must be HatchetConfig for hatchet worker type"
            )


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
class LoggingConfig:
    """Configuration for logging services."""

    development: bool
    log_level: str


@dataclass
class VulkanEngineConfig:
    """Complete configuration for vulkan-engine."""

    app: AppConfig
    database: DatabaseConfig
    logging: LoggingConfig

    # Unified worker configuration
    worker_database: WorkerDatabaseConfig
    worker_service: WorkerServiceConfig

"""Configuration classes for vulkan-engine.

This module defines all configuration dataclasses that vulkan-server
and other implementations can use and extend.
"""

from dataclasses import dataclass
from typing import Literal, Union

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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


class DatabaseConfig(BaseSettings):
    """Configuration for the main application database.

    Automatically loads from environment variables with DB_ prefix.
    Supports .env files and environment variable overrides.
    """

    user: str = Field(..., alias="DB_USER")
    password: str = Field(..., alias="DB_PASSWORD")
    host: str = Field(default="localhost", alias="DB_HOST")
    port: str = Field(default="5432", alias="DB_PORT")
    database: str = Field(..., alias="DB_DATABASE")
    pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    pool_recycle: int = Field(default=3600, alias="DB_POOL_RECYCLE")
    pool_pre_ping: bool = Field(default=True, alias="DB_POOL_PRE_PING")
    echo: bool = Field(default=False, alias="DB_ECHO")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string (postgresql+asyncpg://)."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def sync_connection_string(self) -> str:
        """Get synchronous PostgreSQL connection string (postgresql+psycopg2://) for migrations."""
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class AppConfig:
    """Configuration for the application server."""

    host: str
    port: str
    data_broker_url: str | None = None

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
        """Get PostgreSQL connection string if database is enabled and configured (postgresql+asyncpg://)."""
        if not self.enabled or not all(
            [self.user, self.password, self.host, self.port, self.database]
        ):
            return None
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


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

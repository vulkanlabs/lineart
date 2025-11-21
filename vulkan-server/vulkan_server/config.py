"""Configuration loading for vulkan-server.

This module handles environment variable loading and creates VulkanEngineConfig instances.
"""

import os

from vulkan_engine.backends.factory.service_client import create_worker_service_config
from vulkan_engine.config import (
    AppConfig,
    DatabaseConfig,
    LoggingConfig,
    VulkanEngineConfig,
    WorkerDatabaseConfig,
)


def load_database_config() -> DatabaseConfig:
    """Load database configuration from environment variables.

    DatabaseConfig uses pydantic_settings to automatically load from
    environment variables (DB_USER, DB_PASSWORD, etc.) and .env files.
    """
    return DatabaseConfig()


def load_app_config() -> AppConfig:
    """Load app configuration from environment variables."""
    host = os.getenv("APP_HOST", "localhost")
    port = os.getenv("APP_PORT", "6001")

    return AppConfig(host=host, port=port)


def load_logging_config() -> LoggingConfig:
    """Load logging configuration from environment variables."""
    development = os.getenv("ENVIRONMENT", "development") == "development"
    log_level = os.getenv("LOG_LEVEL", "INFO")

    return LoggingConfig(development=development, log_level=log_level)


def load_worker_database_config() -> WorkerDatabaseConfig:
    """Load worker database configuration from environment variables."""
    enabled = os.getenv("WORKER_DB_ENABLED", "true").lower() in (
        "true",
        "1",
        "yes",
        "on",
    )

    if not enabled:
        return WorkerDatabaseConfig(enabled=False)

    user = os.getenv("WORKER_DB_USER")
    password = os.getenv("WORKER_DB_PASSWORD")
    host = os.getenv("WORKER_DB_HOST")
    port = os.getenv("WORKER_DB_PORT")
    database = os.getenv("WORKER_DB_DATABASE")

    return WorkerDatabaseConfig(
        enabled=enabled,
        user=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def load_vulkan_engine_config() -> VulkanEngineConfig:
    """Load complete VulkanEngineConfig from environment variables."""
    app = load_app_config()
    database = load_database_config()
    logging = load_logging_config()
    worker_database = load_worker_database_config()
    worker_service = create_worker_service_config()

    return VulkanEngineConfig(
        app=app,
        database=database,
        logging=logging,
        worker_database=worker_database,
        worker_service=worker_service,
    )

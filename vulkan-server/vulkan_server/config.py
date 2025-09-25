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
    """Load database configuration from environment variables."""
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    database = os.getenv("DB_DATABASE")

    if not all([user, password, host, port, database]):
        missing = [
            name
            for name, value in [
                ("DB_USER", user),
                ("DB_PASSWORD", password),
                ("DB_HOST", host),
                ("DB_PORT", port),
                ("DB_DATABASE", database),
            ]
            if value is None
        ]
        raise ValueError(
            f"Missing required database environment variables: {', '.join(missing)}"
        )

    return DatabaseConfig(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def load_app_config() -> AppConfig:
    """Load app configuration from environment variables."""
    host = os.getenv("APP_HOST", "localhost")
    port = os.getenv("APP_PORT", "6001")

    return AppConfig(host=host, port=port)


def load_logging_config() -> LoggingConfig:
    """Load logging configuration from environment variables."""
    gcp_project_id = os.getenv("GCP_PROJECT_ID")

    return LoggingConfig(gcp_project_id=gcp_project_id)


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

"""Configuration loading for vulkan-server.

This module handles environment variable loading and creates VulkanEngineConfig instances.
"""

import os

from vulkan_engine.config import (
    SUPPORTED_BACKENDS,
    AppConfig,
    DatabaseConfig,
    ExternalServiceConfig,
    LoggingConfig,
    VulkanEngineConfig,
    WorkerDatabaseConfig,
    WorkerServiceConfig,
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


def load_external_service_config() -> ExternalServiceConfig:
    """Load external service configuration from environment variables."""
    resolution_service_url = os.getenv("RESOLUTION_SERVICE_URL")
    beam_launcher_url = os.getenv("BEAM_LAUNCHER_URL")

    return ExternalServiceConfig(
        resolution_service_url=resolution_service_url,
        beam_launcher_url=beam_launcher_url,
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


def load_worker_service_config() -> WorkerServiceConfig:
    """Load worker service configuration from environment variables."""
    worker_type = os.getenv("WORKER_TYPE")
    if worker_type not in SUPPORTED_BACKENDS:
        raise ValueError(
            f"Invalid WORKER_TYPE: {worker_type}. Must be one of {SUPPORTED_BACKENDS}"
        )

    worker_url = os.getenv("WORKER_URL")
    if worker_url is None:
        raise ValueError("Missing required environment variable: WORKER_URL")

    config = WorkerServiceConfig(
        worker_type=worker_type,
        server_url=worker_url,
    )
    return config


def load_vulkan_engine_config() -> VulkanEngineConfig:
    """Load complete VulkanEngineConfig from environment variables."""
    app = load_app_config()
    database = load_database_config()
    external_services = load_external_service_config()
    logging = load_logging_config()
    worker_database = load_worker_database_config()
    worker_service = load_worker_service_config()

    return VulkanEngineConfig(
        app=app,
        database=database,
        external_services=external_services,
        logging=logging,
        worker_database=worker_database,
        worker_service=worker_service,
    )

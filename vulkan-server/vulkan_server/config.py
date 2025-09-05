"""Configuration loading for vulkan-server.

This module handles environment variable loading and creates VulkanEngineConfig instances.
"""

import os

from vulkan_engine.config import (
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
    worker_type = os.getenv("WORKER_TYPE", "dagster")

    if worker_type not in ("dagster", "hatchet"):
        raise ValueError(
            f"Invalid WORKER_TYPE: {worker_type}. Must be 'dagster' or 'hatchet'"
        )

    host = os.getenv("WORKER_HOST")
    port = os.getenv("WORKER_PORT")

    if not all([host, port]):
        missing = [
            name
            for name, value in [("WORKER_HOST", host), ("WORKER_PORT", port)]
            if value is None
        ]
        raise ValueError(
            f"Missing required worker service environment variables: {', '.join(missing)}"
        )

    # Create base config
    config = WorkerServiceConfig(
        worker_type=worker_type,
        host=host,
        port=port,
    )

    if worker_type == "dagster":
        # Dagster-specific configuration
        server_port = os.getenv("WORKER_SERVER_PORT")
        if not server_port:
            raise ValueError(
                "Missing required environment variable: WORKER_SERVER_PORT"
            )
        config.server_port = server_port

    elif worker_type == "hatchet":
        # Hatchet-specific configuration
        config.home_path = os.getenv("WORKER_HOME")
        config.scripts_path = os.getenv("WORKER_SCRIPTS_PATH")
        config.workspaces_path = os.getenv("WORKER_WORKSPACES_PATH")

        if not config.home_path:
            raise ValueError("Missing required environment variable: WORKER_HOME")

    return config


def load_vulkan_engine_config() -> VulkanEngineConfig:
    """Load complete VulkanEngineConfig from environment variables."""
    # Load worker configuration
    worker_database = load_worker_database_config()
    worker_service = load_worker_service_config()

    return VulkanEngineConfig(
        app=load_app_config(),
        database=load_database_config(),
        external_services=load_external_service_config(),
        logging=load_logging_config(),
        worker_database=worker_database,
        worker_service=worker_service,
    )

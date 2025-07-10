"""Configuration loading for vulkan-server.

This module handles environment variable loading and creates VulkanEngineConfig instances.
"""

import os

from vulkan_engine.config import (
    AppConfig,
    DagsterDatabaseConfig,
    DagsterServiceConfig,
    DatabaseConfig,
    ExternalServiceConfig,
    LoggingConfig,
    VulkanEngineConfig,
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


def load_dagster_database_config() -> DagsterDatabaseConfig:
    """Load Dagster database configuration from environment variables."""
    user = os.getenv("DAGSTER_DB_USER")
    password = os.getenv("DAGSTER_DB_PASSWORD")
    host = os.getenv("DAGSTER_DB_HOST")
    port = os.getenv("DAGSTER_DB_PORT")
    database = os.getenv("DAGSTER_DB_DATABASE")

    if not all([user, password, host, port, database]):
        missing = [
            name
            for name, value in [
                ("DAGSTER_DB_USER", user),
                ("DAGSTER_DB_PASSWORD", password),
                ("DAGSTER_DB_HOST", host),
                ("DAGSTER_DB_PORT", port),
                ("DAGSTER_DB_DATABASE", database),
            ]
            if value is None
        ]
        raise ValueError(
            f"Missing required Dagster database environment variables: {', '.join(missing)}"
        )

    return DagsterDatabaseConfig(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def load_dagster_service_config() -> DagsterServiceConfig:
    """Load Dagster service configuration from environment variables."""
    host = os.getenv("DAGSTER_HOST")
    port = os.getenv("DAGSTER_PORT")
    server_port = os.getenv("DAGSTER_SERVER_PORT")

    if not all([host, port, server_port]):
        missing = [
            name
            for name, value in [
                ("DAGSTER_HOST", host),
                ("DAGSTER_PORT", port),
                ("DAGSTER_SERVER_PORT", server_port),
            ]
            if value is None
        ]
        raise ValueError(
            f"Missing required Dagster service environment variables: {', '.join(missing)}"
        )

    return DagsterServiceConfig(
        host=host,
        port=port,
        server_port=server_port,
    )


def load_external_service_config() -> ExternalServiceConfig:
    """Load external service configuration from environment variables."""
    upload_service_url = os.getenv("UPLOAD_SERVICE_URL")
    resolution_service_url = os.getenv("RESOLUTION_SERVICE_URL")
    beam_launcher_url = os.getenv("BEAM_LAUNCHER_URL")

    if not upload_service_url:
        raise ValueError("Missing required environment variable: UPLOAD_SERVICE_URL")

    return ExternalServiceConfig(
        upload_service_url=upload_service_url,
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


def load_vulkan_engine_config() -> VulkanEngineConfig:
    """Load complete VulkanEngineConfig from environment variables."""
    return VulkanEngineConfig(
        app=load_app_config(),
        database=load_database_config(),
        dagster_database=load_dagster_database_config(),
        dagster_service=load_dagster_service_config(),
        external_services=load_external_service_config(),
        logging=load_logging_config(),
    )

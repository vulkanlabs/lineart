"""
Logging initialization for Vulkan applications.

Provides simple functions for initializing and accessing structlog loggers.
All context injection happens automatically via structlog.contextvars.

Usage:
    # At app startup
    init_logger(development=True)

    # In services
    logger = get_logger(__name__)
    logger.info("processing_request", user_id=user.id)
"""

import structlog
from structlog.stdlib import BoundLogger

from vulkan_engine.logging.config import configure_structlog as _configure_structlog


def init_logger(
    development: bool = False,
    log_level: str = "INFO",
) -> BoundLogger:
    """
    Initialize and configure structlog logging.

    This should be called once at application startup.

    Args:
        development: If True, use pretty console output. If False, use JSON.
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured structlog logger
    """
    # Configure structlog globally
    _configure_structlog(development=development, log_level=log_level)

    # Return a logger instance
    return structlog.get_logger("vulkan_engine")


def get_logger(name: str | None = None) -> BoundLogger:
    """
    Get a structlog logger instance.

    Args:
        name: Logger name, typically __name__ of the calling module

    Returns:
        Configured structlog BoundLogger

    Example:
        logger = get_logger(__name__)
        logger.info("processing_data", record_count=100)
    """
    return structlog.get_logger(name)

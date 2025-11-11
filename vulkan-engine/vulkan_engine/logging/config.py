"""
Structlog configuration for Vulkan applications.

Provides development and production configurations with automatic
context injection from contextvars.
"""

import logging
import sys

import structlog
from structlog.types import Processor


def configure_structlog(
    development: bool = False,
    log_level: str = "INFO",
) -> None:
    """
    Configure structlog for Vulkan applications.

    This should be called once at application startup, typically in
    the FastAPI lifespan handler or main initialization.

    Args:
        development: If True, use console renderer. If False, use JSON.
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    processors: list[Processor] = [
        # Add contextvars first - this gets context from structlog.contextvars
        structlog.contextvars.merge_contextvars,
        # Add log level
        structlog.processors.add_log_level,
        # Add timestamp in ISO format
        structlog.processors.TimeStamper(fmt="iso"),
        # Add caller info (file, line, function)
        structlog.processors.CallsiteParameterAdder(
            parameters=[structlog.processors.CallsiteParameter.QUAL_NAME]
        ),
        # Format exception info
        structlog.processors.format_exc_info,
        # Render stack traces for warnings and above
        structlog.processors.StackInfoRenderer(),
    ]

    if development:
        # Development: Pretty console output with colors
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.rich_traceback,
            )
        )
    else:
        # Production: JSON output for log aggregation
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

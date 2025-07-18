"""
Google Cloud Platform logging integration.

Simple, direct integration with GCP Cloud Logging that gracefully handles
missing dependencies and provides clear configuration options.
"""

import json
import logging
import sys


def create_gcp_handler(
    project_id: str, logger_name: str = "vulkan-server"
) -> logging.Handler | None:
    """
    Create a GCP Cloud Logging handler.

    Args:
        project_id: GCP project ID for cloud logging
        logger_name: Name for the cloud logger (default: "vulkan-server")

    Returns:
        CloudLoggingHandler instance or None if GCP dependencies aren't available
    """
    if not project_id:
        return None

    try:
        import google.cloud.logging
        from google.cloud.logging.handlers import CloudLoggingHandler
    except ImportError:
        # WARNING: This exception is only logged and not propagated.
        # Consider re-raising or handling more robustly to avoid masking critical errors.
        # Graceful degradation when GCP dependencies aren't installed
        logging.getLogger(logger_name).warning(
            "Cloud Logging is not available: install 'google-cloud-logging' to enable cloud logging."
        )
        return None

    try:
        client = google.cloud.logging.Client(project=project_id)
        handler = CloudLoggingHandler(client, name=logger_name, stream=sys.stdout)
        handler.setFormatter(GCPFormatter())
        return handler
    except Exception as e:
        # WARNING: This exception is only logged and not propagated.
        # Consider re-raising or handling more robustly to avoid masking critical errors.
        # Graceful degradation if GCP setup fails (auth, network, etc.)
        logging.getLogger(logger_name).warning(
            f"Failed to initialize Cloud Logging: {e}"
        )
        return None


def is_gcp_available() -> bool:
    """
    Check if GCP Cloud Logging dependencies are available.

    Returns:
        True if google-cloud-logging is installed and importable
    """
    try:
        import google.cloud.logging
        from google.cloud.logging.handlers import CloudLoggingHandler

        return True
    except ImportError:
        return False


class GCPFormatter(logging.Formatter):
    """Custom formatter for GCP Cloud Logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for GCP with enhanced JSON encoding."""
        from vulkan_engine.logger import EnhancedJSONEncoder

        extra = getattr(record, "extra", {})
        log_record = {
            "message": record.getMessage(),
            "extra": extra,
        }
        return json.dumps(log_record, cls=EnhancedJSONEncoder)

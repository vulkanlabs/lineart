"""
Base service class for all Vulkan Engine services.

Provides common functionality like database session and logging.
"""

from abc import ABC
from typing import Any

from sqlalchemy.orm import Session

from vulkan_engine.config import LoggingConfig
from vulkan_engine.logger import VulkanLogger, create_logger


class BaseService(ABC):
    """
    Base class for all service classes.

    Provides:
    - Database session access
    - Logger instance (always available)
    - Common patterns for service operations
    """

    def __init__(self, db: Session, logger: VulkanLogger | None = None):
        """
        Initialize base service.

        Args:
            db: SQLAlchemy database session
            logger: Optional VulkanLogger instance for logging events
        """
        self.db = db
        self.logger = logger or _create_default_logger(db)

    def _log_event(self, event, **kwargs):
        """Helper method to log events."""
        self.logger.event(event, **kwargs)

    def _convert_pydantic_to_dict(self, obj) -> Any:
        """Recursively convert Pydantic models to dictionaries."""
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        elif isinstance(obj, dict):
            return {k: self._convert_pydantic_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_pydantic_to_dict(i) for i in obj]
        else:
            return obj


def _create_default_logger(db: Session) -> VulkanLogger:
    """Create a default logger instance."""
    default_config = LoggingConfig(gcp_project_id=None)
    return create_logger(db, default_config)

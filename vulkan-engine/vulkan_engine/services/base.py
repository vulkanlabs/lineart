"""
Base service class for all Vulkan Engine services.

Provides common functionality like database session and logging.
"""

from abc import ABC

from sqlalchemy.orm import Session

from vulkan_engine.logger import VulkanLogger


class BaseService(ABC):
    """
    Base class for all service classes.

    Provides:
    - Database session access
    - Optional logger instance
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
        self.logger = logger

    def _log_event(self, event, **kwargs):
        """Helper method to log events if logger is available."""
        if self.logger:
            self.logger.event(event, **kwargs)

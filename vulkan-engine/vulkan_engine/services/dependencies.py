"""
Dependency injection helpers for services.

These functions are used by FastAPI routers to inject service instances.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from vulkan_engine.db import get_db
from vulkan_engine.logger import VulkanLogger, get_logger


def get_service_dependencies(
    db: Session = Depends(get_db),
    logger: VulkanLogger | None = Depends(get_logger),
) -> tuple[Session, VulkanLogger | None]:
    """
    Get common dependencies for services.

    Returns:
        Tuple of (database session, logger)
    """
    return db, logger

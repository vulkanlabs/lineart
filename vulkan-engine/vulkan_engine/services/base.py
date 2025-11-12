"""
Base service class for all Vulkan Engine services.

Provides common functionality like database session access.
"""

from abc import ABC
from typing import Any

from sqlalchemy.orm import Session


class BaseService(ABC):
    """
    Base class for all service classes.

    Provides:
    - Database session access
    - Common patterns for service operations

    Services that need logging should instantiate their own logger:
        from vulkan_engine.logging import get_logger
        logger = get_logger(__name__)
    """

    def __init__(self, db: Session):
        """
        Initialize base service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

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

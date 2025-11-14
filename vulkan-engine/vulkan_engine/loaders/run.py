"""
Run loader for data access operations.

Provides centralized run data access with consistent filtering and error handling.
"""

from sqlalchemy import select

from vulkan_engine.db import Run
from vulkan_engine.exceptions import RunNotFoundException
from vulkan_engine.loaders.base import BaseLoader


class RunLoader(BaseLoader):
    """Loader for run data access operations."""

    async def get_run(self, run_id: str, project_id: str | None = None) -> Run:
        """
        Get a run by ID, optionally filtered by project.

        Args:
            run_id: Run UUID
            project_id: Optional project UUID to filter by

        Returns:
            Run object

        Raises:
            RunNotFoundException: If run doesn't exist or doesn't belong to specified project
        """
        stmt = select(Run).filter_by(run_id=run_id, project_id=project_id)
        result = await self.db.execute(stmt)
        run = result.scalar_one_or_none()

        if not run:
            raise RunNotFoundException(f"Run {run_id} not found")

        return run

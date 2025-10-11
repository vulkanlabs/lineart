"""
Run loader for data access operations.

Provides centralized run data access with consistent filtering and error handling.
"""

from vulkan_engine.db import Run
from vulkan_engine.exceptions import RunNotFoundException
from vulkan_engine.loaders.base import BaseLoader


class RunLoader(BaseLoader):
    """Loader for run data access operations."""

    def get_run(self, run_id: str, project_id: str | None = None) -> Run:
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
        run = self.db.query(Run).filter_by(run_id=run_id, project_id=project_id).first()

        if not run:
            raise RunNotFoundException(f"Run {run_id} not found")

        return run

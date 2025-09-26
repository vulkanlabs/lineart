from abc import ABC, abstractmethod

from requests import Response


class BackendServiceClient(ABC):
    """Abstract base class for workflow engine service clients."""

    @abstractmethod
    def update_workspace(
        self,
        workspace_id: str,
        spec: dict | None = None,
        requirements: list[str] | None = None,
    ) -> Response:
        """Create or update a workspace.

        Args:
            workspace_id: Unique identifier for the workspace
            spec: Workflow specification dictionary
            requirements: List of Python package requirements

        Returns:
            HTTP response from the service
        """
        pass

    @abstractmethod
    def get_workspace(self, workspace_id: str) -> Response:
        """Get information about a workspace.

        Args:
            workspace_id: Unique identifier for the workspace

        Returns:
            HTTP response with workspace information
        """
        pass

    @abstractmethod
    def delete_workspace(self, workspace_id: str) -> Response:
        """Delete a workspace.

        Args:
            workspace_id: Unique identifier for the workspace

        Returns:
            HTTP response from the service
        """
        pass

    @abstractmethod
    def ensure_workspace_added(self, workspace_id: str) -> None:
        """Ensure that the workspace has been successfully added.

        Args:
            workspace_id: Unique identifier for the workspace

        Raises:
            ValueError: If the workspace was not successfully added
        """
        pass

    @abstractmethod
    def ensure_workspace_removed(self, workspace_id: str) -> None:
        """Ensure that the workspace has been successfully removed.

        Args:
            workspace_id: Unique identifier for the workspace

        Raises:
            ValueError: If the workspace was not successfully removed
        """
        pass
        pass

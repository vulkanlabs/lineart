import os
from abc import ABC, abstractmethod

from uuid import uuid4
import pandas as pd


class FileManager(ABC):
    @abstractmethod
    def publish(self, project_id: str, data: pd.DataFrame) -> str:
        pass

    @abstractmethod
    def delete(self, project_id: str, public_filepath: str) -> None:
        pass

    @abstractmethod
    def get(self, project_id: str, public_filepath: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def public_filepath(self, project_id: str) -> str:
        """Generate a public identifier for the file."""
        pass

    @abstractmethod
    def private_filepath(self, public_filepath: str) -> str:
        """Convert a public identifier to a backend-specific file path."""
        pass

    def _ensure_subdir(self, project_id: str, filepath: str) -> None:
        if not filepath.startswith(os.path.join(self.base_dir, project_id)):
            raise ValueError(f"Filepath not in project files: {filepath}")

    @staticmethod
    def _gen_file_id() -> str:
        return str(uuid4())
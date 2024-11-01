import os
from abc import ABC, abstractmethod

import pandas as pd


class FileManager(ABC):
    @abstractmethod
    def publish(self, project_id: str, data: pd.DataFrame) -> str:
        pass

    @abstractmethod
    def delete(self, project_id: str, file_path: str) -> None:
        pass

    @abstractmethod
    def get(self, project_id: str, file_path: str) -> pd.DataFrame:
        pass

    def _ensure_subdir(self, project_id: str, filepath: str) -> None:
        if not filepath.startswith(os.path.join(self.base_dir, project_id)):
            raise ValueError(f"Filepath not in project: {filepath}")
        if not filepath.startswith(os.path.join(self.base_dir, project_id)):
            raise ValueError(f"Filepath not in project: {filepath}")

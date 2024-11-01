import os
from uuid import uuid4

import pandas as pd

from upload_svc.manager.base import FileManager


class LocalFileManager(FileManager):
    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def publish(self, project_id: str, data: pd.DataFrame) -> str:
        filepath = self._filepath(project_id, file_id=str(uuid4()))

        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            data.to_parquet(filepath)
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise ValueError(f"Failed to publish file: {e}")

        return filepath

    def delete(self, project_id: str, filepath: str) -> None:
        self._ensure_subdir(project_id, filepath)
        if os.path.exists(filepath):
            os.remove(filepath)

    def get(self, project_id: str, filepath: str) -> pd.DataFrame:
        if not os.path.exists(filepath):
            raise ValueError(f"File not found: {filepath}")

        self._ensure_subdir(project_id, filepath)
        return pd.read_parquet(filepath)

    def _filepath(self, project_id: str, file_id: str) -> str:
        return os.path.join(self.base_dir, project_id, file_id)

    def _ensure_subdir(self, project_id: str, filepath: str) -> None:
        if not filepath.startswith(os.path.join(self.base_dir, project_id)):
            raise ValueError(f"Filepath not in project: {filepath}")
        if not filepath.startswith(os.path.join(self.base_dir, project_id)):
            raise ValueError(f"Filepath not in project: {filepath}")

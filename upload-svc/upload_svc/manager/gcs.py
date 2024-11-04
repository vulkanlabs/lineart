import os
from uuid import uuid4

import pandas as pd
from gcsfs import GCSFileSystem

from upload_svc.manager.base import FileManager


class GCSFileManager(FileManager):
    def __init__(self, gcp_project: str, bucket_name: str, base_path: str) -> None:
        self.gcp_project = gcp_project
        self.bucket_name = bucket_name
        self.base_path = base_path
        self.fs = GCSFileSystem(project=self.gcp_project, access="read_write")

    def publish(self, project_id: str, data: pd.DataFrame) -> str:
        filepath = self._filepath(project_id, file_id=str(uuid4()))

        try:
            with self.fs.open(filepath, "wb") as f:
                data.to_parquet(f)
        except Exception as e:
            if self.fs.exists(filepath):
                self.fs.rm(filepath, recursive=True)
            raise ValueError(f"Failed to publish file: {e}")

        return filepath

    def delete(self, project_id: str, filepath: str) -> None:
        self._ensure_subdir(project_id, filepath)
        if os.path.exists(filepath):
            os.remove(filepath)

    def get(self, project_id: str, filepath: str) -> pd.DataFrame:
        if not self.fs.exists(filepath):
            raise ValueError(f"File not found: {filepath}")

        self._ensure_subdir(project_id, filepath)
        with self.fs.open(filepath, "rb") as f:
            return pd.read_parquet(f)

    def _filepath(self, project_id: str, file_id: str) -> str:
        return os.path.join(self.bucket_name, self.base_path, project_id, file_id)

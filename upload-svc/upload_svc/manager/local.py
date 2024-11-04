import os

import pandas as pd

from upload_svc.manager.base import FileManager


class LocalFileManager(FileManager):
    def __init__(self, base_path: str) -> None:
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def publish(self, project_id: str, data: pd.DataFrame) -> str:
        public_path = self.public_filepath(project_id)
        filepath = self.private_filepath(public_path)

        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            data.to_parquet(filepath)
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise ValueError(f"Failed to publish file: {e}")

        return public_path

    def delete(self, project_id: str, public_filepath: str) -> None:
        filepath = self.private_filepath(public_filepath)
        self._ensure_subdir(project_id, filepath)
        if os.path.exists(filepath):
            os.remove(filepath)

    def get(self, project_id: str, public_filepath: str) -> pd.DataFrame:
        filepath = self.private_filepath(public_filepath)
        if not os.path.exists(filepath):
            raise ValueError(f"File not found: {filepath}")

        self._ensure_subdir(project_id, filepath)
        return pd.read_parquet(filepath)

    def public_filepath(self, project_id: str) -> str:
        file_id = self._gen_file_id()
        return f"file://{self.base_path}/{project_id}/{file_id}"

    def private_filepath(self, public_filepath: str) -> str:
        if not public_filepath.startswith("file://"):
            raise ValueError(f"Invalid file path: {public_filepath}")
        return public_filepath.replace("file://", "")

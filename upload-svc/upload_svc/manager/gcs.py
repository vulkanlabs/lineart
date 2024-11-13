import pandas as pd
from gcsfs import GCSFileSystem

from upload_svc.manager.base import FileManager


class GCSFileManager(FileManager):
    def __init__(
        self, gcp_project: str, bucket_name: str, base_path: str, token: str
    ) -> None:
        self.gcp_project = gcp_project
        self.bucket_name = bucket_name
        self.base_path = base_path
        self.fs = GCSFileSystem(
            project=self.gcp_project, access="read_write", token=token
        )

    def publish(self, project_id: str, data: pd.DataFrame) -> str:
        public_path = self.public_filepath(project_id)
        filepath = self.private_filepath(public_path)

        try:
            with self.fs.open(filepath, "wb") as f:
                data.to_parquet(f)
        except Exception as e:
            if self.fs.exists(filepath):
                self.fs.rm(filepath, recursive=True)
            raise ValueError(f"Failed to publish file: {e}")

        return public_path

    def delete(self, project_id: str, public_filepath: str) -> None:
        filepath = self.private_filepath(public_filepath)
        self._ensure_subdir(project_id, filepath)
        if self.fs.exists(filepath):
            self.fs.rm(filepath, recursive=True)

    def get(self, project_id: str, public_filepath: str) -> pd.DataFrame:
        filepath = self.private_filepath(public_filepath)
        if not self.fs.exists(filepath):
            raise ValueError(f"File not found: {filepath}")

        self._ensure_subdir(project_id, filepath)
        with self.fs.open(filepath, "rb") as f:
            return pd.read_parquet(f)

    def public_filepath(self, project_id: str) -> str:
        file_id = self._gen_file_id()
        return f"gs://{self.bucket_name}/{self.base_path}/{project_id}/{file_id}"

    def private_filepath(self, public_filepath: str) -> str:
        if not public_filepath.startswith("gs://"):
            raise ValueError(f"Invalid GCS path: {public_filepath}")
        return public_filepath.replace("gs://", "")

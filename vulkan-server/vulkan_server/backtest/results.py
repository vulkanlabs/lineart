import os

import pandas as pd
from gcsfs import GCSFileSystem
from pyarrow import parquet

from vulkan_server.logger import init_logger


class ResultsDB:
    def __init__(self, gcp_project_id: str, token_path: str) -> None:
        self.fs = GCSFileSystem(
            project=gcp_project_id, access="read_write", token=token_path
        )
        self.logger = init_logger("ResultsDB")
        _ = self.fs.ls("")  # check if credentials are valid

    def load_data(self, paths: str | list[str]) -> pd.DataFrame:
        if isinstance(paths, str):
            paths = [paths]

        for path in paths:
            try:
                exists = self.fs.exists(path)
            except Exception:
                raise ValueError(f"Failed to check if {path} exists")

            if not exists:
                raise ValueError(f"Path {path} does not exist")

        file_paths = []
        for path in paths:
            file_paths.extend(self.fs.ls(path))

        if len(file_paths) == 0:
            raise ValueError("No files found")

        self.logger.info(f"Loading {len(file_paths)} files from {len(paths)} paths")
        ds = parquet.ParquetDataset(file_paths, filesystem=self.fs)
        return ds.read().to_pandas()
    
    # FIXME
    def load_metrics(self, path: str) -> pd.DataFrame:
        with self.fs.open(path, "rb") as f:
            return pd.read_json(f, lines=True)


def make_results_db() -> ResultsDB:
    token_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    gcp_project_id = os.environ.get("GCP_PROJECT_ID")
    if token_path is None:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set")
    if gcp_project_id is None:
        raise ValueError("GCP_PROJECT_ID not set")
    return ResultsDB(gcp_project_id, token_path)

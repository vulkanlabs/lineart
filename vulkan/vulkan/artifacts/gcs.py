from gcsfs import GCSFileSystem


class GCSArtifactManager:
    def __init__(self, project_id: str, bucket_name: str, token: str) -> None:
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.gcs = GCSFileSystem(
            project=self.project_id,
            access="read_write",
            token=token,
        )

    def post_file(self, from_path: str, to_path: str) -> str:
        full_path = f"{self.bucket_name}/{to_path}"
        self.gcs.put(from_path, full_path)
        return f"gs://{full_path}"

    def post(self, path: str, repository: bytes) -> str:
        full_path = f"{self.bucket_name}/{path}"
        with self.gcs.open(full_path, "wb") as f:
            f.write(repository)

        return f"gs://{full_path}"

    def get(self, path: str) -> bytes:
        path = f"{self.bucket_name}/{path}"
        with self.gcs.open(path, "rb") as f:
            return f.read()

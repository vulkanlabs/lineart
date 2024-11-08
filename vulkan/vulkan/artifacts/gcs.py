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

    def post(self, path: str, repository: bytes):
        path = f"{self.bucket_name}/{path}"
        with self.gcs.open(path, "wb") as f:
            f.write(repository)

    def get(self, path: str) -> bytes:
        path = f"{self.bucket_name}/{path}"
        with self.gcs.open(path, "rb") as f:
            return f.read()

import logging
import os
import tarfile
from datetime import datetime, timedelta
from enum import Enum
from time import sleep

from google.cloud.devtools import cloudbuild_v1 as cloudbuild
from jinja2 import Environment, FileSystemLoader
from pydantic.dataclasses import dataclass
from vulkan_public.spec.environment.packing import ARCHIVE_FORMAT, TAR_FLAGS

logger = logging.getLogger("uvicorn.error.Build")


@dataclass
class PackageSpec:
    name: str
    path: str


class _BuildStatus(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"


@dataclass
class _Build:
    name: str
    id: str
    status: _BuildStatus

    _STATUS_MAP = {
        # Success
        cloudbuild.Build.Status.SUCCESS: _BuildStatus.SUCCESS,
        # Progress states
        cloudbuild.Build.Status.STATUS_UNKNOWN: _BuildStatus.IN_PROGRESS,
        cloudbuild.Build.Status.PENDING: _BuildStatus.IN_PROGRESS,
        cloudbuild.Build.Status.QUEUED: _BuildStatus.IN_PROGRESS,
        cloudbuild.Build.Status.WORKING: _BuildStatus.IN_PROGRESS,
        # Failure states
        cloudbuild.Build.Status.FAILURE: _BuildStatus.FAILURE,
        cloudbuild.Build.Status.INTERNAL_ERROR: _BuildStatus.FAILURE,
        cloudbuild.Build.Status.TIMEOUT: _BuildStatus.FAILURE,
        cloudbuild.Build.Status.CANCELLED: _BuildStatus.FAILURE,
        cloudbuild.Build.Status.EXPIRED: _BuildStatus.FAILURE,
    }

    @classmethod
    def from_cloudbuild_build(cls, build: cloudbuild.Build):
        status = cls._STATUS_MAP[build.status]
        return cls(name=build.name, id=build.id, status=status)


class GCPBuildManager:
    def __init__(
        self,
        gcp_project_id: str,
        gcp_region: str,
        gcp_repository_name: str,
    ):
        self.gcp_project_id = gcp_project_id
        self.gcp_region = gcp_region
        self.gcp_repository_name = gcp_repository_name
        self._cloudbuild_client = cloudbuild.CloudBuildClient()

    def build_base_image(
        self,
        bucket_name: str,
        context_file: str,
        image_name: str,
        image_tag: str,
    ) -> str:
        image_path = os.path.join(
            f"{self.gcp_region}-docker.pkg.dev",
            self.gcp_project_id,
            self.gcp_repository_name,
            f"{image_name}:{image_tag}",
        )

        request = {
            "source": {
                "storage_source": {
                    "bucket": bucket_name,
                    "object_": context_file,
                }
            },
            "steps": [
                {
                    "id": "image",
                    "name": "gcr.io/cloud-builders/docker",
                    "args": [
                        "build",
                        "-t",
                        image_path,
                        ".",
                    ],
                },
            ],
            "images": [image_path],
        }
        build = self._run_job(request, timeout_seconds=60, update_interval_seconds=10)
        logger.info(f"Finished build ({build.id}) for image {image_path}")

        return image_path

    def build_beam_image(
        self,
        bucket_name: str,
        context_file: str,
        image_name: str,
        image_tag: str,
    ) -> str:
        image_path = os.path.join(
            f"{self.gcp_region}-docker.pkg.dev",
            self.gcp_project_id,
            self.gcp_repository_name,
            f"{image_name}:{image_tag}",
        )

        request = {
            "source": {
                "storage_source": {
                    "bucket": bucket_name,
                    "object": context_file,
                }
            },
            "steps": [
                {
                    "id": "image",
                    "name": "gcr.io/cloud-builders/docker",
                    "args": [
                        "build",
                        "-t",
                        image_path,
                        ".",
                    ],
                },
                {
                    "id": "build-flex-template",
                    "name": "gcr.io/google.com/cloudsdktool/cloud-sdk",
                    "args": [
                        "gcloud",
                        "dataflow",
                        "flex-template",
                        "build",
                        f"gs://{bucket_name}/build-assets/flex-template/{image_name}.json",
                        "--image",
                        image_path,
                        "--sdk-language",
                        "PYTHON",
                        "--project",
                        self.gcp_project_id,
                    ],
                    "wait_for": ["image"],
                },
            ],
            "images": [image_path],
        }
        build = self._run_job(request, timeout_seconds=300, update_interval_seconds=20)
        logger.info(f"Finished build ({build.id}) for image {image_path}")

        return image_path

    def _run_job(
        self,
        request: dict,
        timeout_seconds: int,
        update_interval_seconds: int = 5,
    ) -> _Build:
        create_request = cloudbuild.CreateBuildRequest(
            parent=f"projects/{self.gcp_project_id}/locations/{self.gcp_region}",
            project_id=self.gcp_project_id,
            build=request,
        )
        create_op = self._cloudbuild_client.create_build(request=create_request)

        build = _Build(
            name=create_op.metadata.build.name,
            id=create_op.metadata.build.id,
            status=_BuildStatus.IN_PROGRESS,
        )

        timeout = timedelta(seconds=timeout_seconds)
        start_time = datetime.now()
        while (datetime.now() - start_time) <= timeout:
            build = self._get_build(build.id)

            if build.status == _BuildStatus.FAILURE:
                raise ValueError(f"failed to create image: build failed {build.id}")
            if build.status == _BuildStatus.SUCCESS:
                return build
            sleep(update_interval_seconds)

        build = self._cancel_build(id=build.id)
        if build.status == _BuildStatus.FAILURE:
            raise ValueError(f"failed to create image: build timed out {build.id}")
        # The build didn't get canceled, it finished before the cancellation.
        return build

    def _get_build(self, build_id: str) -> _Build:
        request = cloudbuild.GetBuildRequest(
            name=f"projects/{self.gcp_project_id}/locations/{self.gcp_region}/builds/{build_id}",
            project_id=self.gcp_project_id,
            id=build_id,
        )
        response = self._cloudbuild_client.get_build(request=request)
        return _Build.from_cloudbuild_build(response)

    def _cancel_build(self, build_id: str) -> _Build:
        request = cloudbuild.CancelBuildRequest(
            project_id=self.gcp_project_id,
            id=build_id,
        )
        response = self._cloudbuild_client.cancel_build(request=request)
        return _Build.from_cloudbuild_build(response)

    # def _trigger_job(
    #     self, image_name: str, image_path: str, request: dict
    # ) -> tuple[str, dict]:
    #     request_file_path = f"/tmp/{image_name}.request.json"
    #     if os.path.exists(request_file_path):
    #         os.remove(request_file_path)
    #     with open(request_file_path, "w") as fp:
    #         json.dump(request, fp)

    #     access_token = _get_access_token()
    #     artifact_registry = f"https://cloudbuild.googleapis.com/v1/projects/{self.gcp_project_id}/locations/{self.gcp_region}/builds"

    #     completed_process = subprocess.run(
    #         [
    #             "curl",
    #             "-X",
    #             "POST",
    #             "-T",
    #             request_file_path,
    #             "-H",
    #             f"Authorization: Bearer {access_token}",
    #             artifact_registry,
    #         ],
    #         stdout=subprocess.PIPE,
    #     )

    #     if os.path.exists(request_file_path):
    #         os.remove(request_file_path)

    #     if completed_process.returncode != 0:
    #         msg = f"Failed to trigger job: {completed_process.stderr}"
    #         raise Exception(msg)

    #     response = json.loads(completed_process.stdout)

    #     return image_path, response


def get_gcp_build_manager() -> GCPBuildManager:
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_REGION = os.getenv("GCP_REGION")
    GCP_REPOSITORY_NAME = os.getenv("GCP_REPOSITORY_NAME")

    if not GCP_PROJECT_ID or not GCP_REGION or not GCP_REPOSITORY_NAME:
        raise ValueError("GCP configuration missing")

    return GCPBuildManager(
        gcp_project_id=GCP_PROJECT_ID,
        gcp_region=GCP_REGION,
        gcp_repository_name=GCP_REPOSITORY_NAME,
    )


# def _get_access_token() -> str:
#     completed_process = subprocess.run(
#         ["gcloud", "auth", "application-default", "print-access-token"],
#         stdout=subprocess.PIPE,
#     )

#     if completed_process.returncode != 0:
#         msg = f"Failed to get access token: {completed_process.stderr}"
#         raise Exception(msg)

#     return completed_process.stdout.decode().strip("\n")


def prepare_base_image_context(
    server_path: str,
    workspace_name: str,
    workspace_path: str,
    components_path: str,
    dependencies: list[str],
    python_version: str,
):
    policy_spec = PackageSpec(name=workspace_name, path=workspace_path)
    dependency_specs = [
        PackageSpec(name=dep, path=f"{components_path}/{dep}") for dep in dependencies
    ]

    base_dockerfile_path = f"{workspace_path}/Dockerfile"
    dockerfile = _render_dockerfile(
        server_path,
        template="Dockerfile.j2",
        python_version=python_version,
        policy=policy_spec,
        dependencies=dependency_specs,
    )
    with open(base_dockerfile_path, "w") as fp:
        fp.write(dockerfile)

    return _pack_policy_build_context(
        name=workspace_name,
        base_dockerfile=base_dockerfile_path,
        policy=policy_spec,
        dependencies=dependency_specs,
    )


def prepare_beam_image_context(
    name: str,
    base_image: str,
    server_path: str,
    python_version: str,
    beam_sdk_version: str,
    flex_template_base_image: str,
) -> str:
    dockerfile_path = "/tmp/Dockerfile"
    dockerfile = _render_dockerfile(
        server_path,
        template="Beam-Dockerfile.j2",
        base_image=base_image,
        python_version=python_version,
        beam_sdk_version=beam_sdk_version,
        flex_template_base_image=flex_template_base_image,
    )
    with open(dockerfile_path, "w") as fp:
        fp.write(dockerfile)

    filename = f"/tmp/beam-{name}.{ARCHIVE_FORMAT}"
    with tarfile.open(name=filename, mode=TAR_FLAGS) as tf:
        tf.add(name=dockerfile_path, arcname="Dockerfile")
        tf.add(
            name=f"{server_path}/resolution-svc/resolution_svc/templates/launch_dataflow.py",
            arcname="launch_dataflow.py",
        )

    return filename


def _render_dockerfile(base_dir: str, template: str, **kwargs):
    env = Environment(
        loader=FileSystemLoader(f"{base_dir}/resolution-svc/resolution_svc/templates")
    )
    dockerfile_template = env.get_template(template)

    return dockerfile_template.render(**kwargs)


def _pack_policy_build_context(
    name: str,
    base_dockerfile: str,
    policy: PackageSpec,
    dependencies: list[PackageSpec],
) -> str:
    basename = f".tmp.{name}"
    filename = f"{basename}.{ARCHIVE_FORMAT}"
    try:
        with tarfile.open(name=filename, mode=TAR_FLAGS) as tf:
            tf.add(name="vulkan-public", arcname="vulkan-public", filter=_tar_filter_fn)
            tf.add(name="vulkan", arcname="vulkan", filter=_tar_filter_fn)

            tf.add(base_dockerfile, arcname="Dockerfile")
            tf.add(policy.path, arcname=os.path.basename(policy.name))
            for dep in dependencies:
                tf.add(dep.path, arcname=os.path.basename(dep.name))
    except Exception as e:
        if os.path.exists(filename):
            os.remove(filename)

        raise RuntimeError(f"Failed to pack policy build context: {e}")

    return filename


def _tar_filter_fn(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
    _EXCLUDE_PATHS = [".git", ".venv", ".vscode"]
    for path in _EXCLUDE_PATHS:
        if path in info.name:
            return None
    return info

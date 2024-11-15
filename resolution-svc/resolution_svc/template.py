import json
import os
import subprocess
import tarfile
from dataclasses import dataclass

from jinja2 import Environment, FileSystemLoader
from vulkan_public.spec.environment.packing import ARCHIVE_FORMAT, TAR_FLAGS


@dataclass
class PackageSpec:
    name: str
    path: str


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

    def trigger_base_cloudbuild_job(
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
                "storageSource": {
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
            ],
            "images": [image_path],
        }

        return self._trigger_job(image_name, image_path, request)

    def trigger_beam_cloudbuild_job(
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
                "storageSource": {
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
                    "waitFor": ["image"],
                },
            ],
            "images": [image_path],
        }

        return self._trigger_job(image_name, image_path, request)

    def _trigger_job(
        self, image_name: str, image_path: str, request: dict
    ) -> tuple[str, dict]:
        request_file_path = f"/tmp/{image_name}.request.json"
        if os.path.exists(request_file_path):
            os.remove(request_file_path)
        with open(request_file_path, "w") as fp:
            json.dump(request, fp)

        access_token = _get_access_token()
        artifact_registry = f"https://cloudbuild.googleapis.com/v1/projects/{self.gcp_project_id}/locations/{self.gcp_region}/builds"

        completed_process = subprocess.run(
            [
                "curl",
                "-X",
                "POST",
                "-T",
                request_file_path,
                "-H",
                f"Authorization: Bearer {access_token}",
                artifact_registry,
            ],
            stdout=subprocess.PIPE,
        )

        if os.path.exists(request_file_path):
            os.remove(request_file_path)

        if completed_process.returncode != 0:
            msg = f"Failed to trigger job: {completed_process.stderr}"
            raise Exception(msg)

        response = json.loads(completed_process.stdout)

        return image_path, response


def _get_access_token() -> str:
    completed_process = subprocess.run(
        ["gcloud", "auth", "application-default", "print-access-token"],
        stdout=subprocess.PIPE,
    )

    if completed_process.returncode != 0:
        msg = f"Failed to get access token: {completed_process.stderr}"
        raise Exception(msg)

    return completed_process.stdout.decode().strip("\n")


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
):
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
) -> bytes:
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

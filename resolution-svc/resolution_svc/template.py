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


def render_dockerfile(
    base_dir: str,
    policy: PackageSpec,
    dependencies: list[PackageSpec],
):
    env = Environment(
        loader=FileSystemLoader(f"{base_dir}/resolution-svc/resolution_svc/templates")
    )
    dockerfile_template = env.get_template("Dockerfile.j2")

    return dockerfile_template.render(
        policy=policy,
        dependencies=dependencies,
        python_version="3.12",
    )


@dataclass
class GCPBuildConfig:
    project_id: str
    region: str
    repository_name: str


class GCPImageBuildManager:
    def __init__(
        self,
        server_path: str,
        workspace_name: str,
        workspace_path: str,
        components_path: str,
        config: GCPBuildConfig,
    ):
        self.server_path = server_path
        self.workspace_name = workspace_name
        self.workspace_path = workspace_path
        self.components_path = components_path

        self.gcp_region = config.region
        self.gcp_project_id = config.project_id
        self.gcp_repository_name = config.repository_name

    def prepare_docker_build_context(self, dependencies: list[str]):
        policy_spec = PackageSpec(name=self.workspace_name, path=self.workspace_path)
        dependency_specs = [
            PackageSpec(name=dep, path=f"{self.components_path}/{dep}")
            for dep in dependencies
        ]
        dockerfile_path = self._render_dockerfile(policy_spec, dependency_specs)

        return pack_policy_build_context(
            name=self.workspace_name,
            dockerfile_path=dockerfile_path,
            policy=policy_spec,
            dependencies=dependency_specs,
        )

    def _render_dockerfile(
        self, policy_spec: PackageSpec, dependency_specs: list[PackageSpec]
    ) -> str:
        dockerfile_path = f"{self.workspace_path}/Dockerfile"
        dockerfile = render_dockerfile(self.server_path, policy_spec, dependency_specs)
        with open(dockerfile_path, "w") as fp:
            fp.write(dockerfile)

        return dockerfile_path

    def trigger_cloudbuild_job(
        self,
        bucket_name: str,
        context_file: str,
        image_name: str,
    ) -> None:
        image_path = os.path.join(
            f"{self.gcp_region}-docker.pkg.dev",
            self.gcp_project_id,
            self.gcp_repository_name,
            f"{image_name}:base",
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
                    "name": "gcr.io/cloud-builders/docker",
                    "args": [
                        "build",
                        "-t",
                        image_path,
                        ".",
                    ],
                }
            ],
            "images": [image_path],
        }

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

        return None


def _get_access_token() -> str:
    completed_process = subprocess.run(
        ["gcloud", "auth", "application-default", "print-access-token"],
        stdout=subprocess.PIPE,
    )

    if completed_process.returncode != 0:
        msg = f"Failed to get access token: {completed_process.stderr}"
        raise Exception(msg)

    return completed_process.stdout.decode().strip("\n")


def pack_policy_build_context(
    name: str,
    dockerfile_path: str,
    policy: PackageSpec,
    dependencies: list[PackageSpec],
) -> bytes:
    basename = f".tmp.{name}"
    filename = f"{basename}.{ARCHIVE_FORMAT}"
    try:
        with tarfile.open(name=filename, mode=TAR_FLAGS) as tf:
            tf.add(name="vulkan-public", arcname="vulkan-public", filter=_tar_filter_fn)
            tf.add(name="vulkan", arcname="vulkan", filter=_tar_filter_fn)

            tf.add(dockerfile_path, arcname="Dockerfile")
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

import os
import subprocess
from shutil import rmtree

from vulkan.artifacts.gcs import GCSArtifactManager
from vulkan_public.spec.environment.packing import unpack_workspace
from vulkan_public.spec.environment.workspace import VulkanCodeLocation

VULKAN_HOME = os.getenv("VULKAN_HOME")
VENVS_PATH = os.getenv("VULKAN_VENVS_PATH")
SCRIPTS_PATH = os.getenv("VULKAN_SCRIPTS_PATH")

WORKSPACES_PATH = f"{VULKAN_HOME}/workspaces"


class VulkanWorkspaceManager:
    def __init__(self, project_id: str, workspace_name: str) -> None:
        self.project_id = project_id
        self.workspace_name = workspace_name
        self.workspace_path = f"{WORKSPACES_PATH}/{self.workspace_name}"
        self._code_location = None

    @property
    def components_path(self) -> str:
        return f"{VULKAN_HOME}/components/{self.project_id}"

    @property
    def code_location(self) -> VulkanCodeLocation:
        if self._code_location is None:
            self._code_location = VulkanCodeLocation.from_workspace(self.workspace_path)
        return self._code_location

    def unpack_workspace(self, artifacts: GCSArtifactManager, name: str) -> str:
        repository = artifacts.get(f"{self.project_id}/policy/{name}.tar.gz")
        workspace_path = unpack_workspace(
            WORKSPACES_PATH, self.workspace_name, repository
        )
        return workspace_path

    def create_venv(self) -> str:
        return _create_venv_for_workspace(
            f"{VENVS_PATH}/{self.workspace_name}", self.workspace_path
        )

    def install_components(
        self, artifacts: GCSArtifactManager, required_components: list[str]
    ):
        for component in required_components:
            component_path = f"{self.project_id}/component/{component}.tar.gz"
            component_code = artifacts.get(component_path)
            self._unpack_component(component, component_code)

        _install_components(
            self.workspace_name, self.components_path, required_components
        )

    def _unpack_component(self, alias: str, repository: bytes) -> str:
        return unpack_workspace(self.components_path, alias, repository)

    def delete_resources(self):
        rmtree(self.workspace_path)
        rmtree(f"{VENVS_PATH}/{self.workspace_name}")


def _create_venv_for_workspace(venv_path, workspace_path):
    completed_process = subprocess.run(
        [
            "bash",
            f"{SCRIPTS_PATH}/create_venv.sh",
            venv_path,
            workspace_path,
        ],
        capture_output=True,
    )
    if completed_process.returncode != 0:
        msg = f"Failed to create virtual environment: {completed_process.stderr}"
        raise Exception(msg)
    return venv_path


def _install_components(workspace_name, components_base_dir, required_components):
    for component_alias in required_components:
        component_path = os.path.join(components_base_dir, component_alias)
        completed_process = subprocess.run(
            [
                "bash",
                f"{SCRIPTS_PATH}/install_component.sh",
                workspace_name,
                component_path,
            ],
            capture_output=True,
        )
        if completed_process.returncode != 0:
            raise Exception(f"Failed to install component: {component_alias}")

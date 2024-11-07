import os
import subprocess
from shutil import rmtree

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
    def venv_path(self) -> str:
        return f"{VENVS_PATH}/{self.workspace_name}"

    @property
    def components_path(self) -> str:
        return f"{VULKAN_HOME}/components/{self.project_id}"

    @property
    def code_location(self) -> VulkanCodeLocation:
        if self._code_location is None:
            self._code_location = VulkanCodeLocation.from_workspace(self.workspace_path)
        return self._code_location

    def unpack_workspace(self, repository: bytes) -> str:
        workspace_path = unpack_workspace(
            WORKSPACES_PATH, self.workspace_name, repository
        )
        return workspace_path

    def create_venv(self):
        process = subprocess.run(
            [
                "bash",
                f"{SCRIPTS_PATH}/create_venv.sh",
                self.venv_path,
                self.workspace_path,
            ],
            capture_output=True,
        )
        if process.returncode != 0:
            msg = f"Failed to create virtual environment: {process.stderr}"
            raise Exception(msg)
        return self.venv_path

    def install_components(self, required_components: list[str]):
        for component in required_components:
            location = os.path.join(self.components_path, component)
            process = subprocess.run(
                [
                    "bash",
                    f"{SCRIPTS_PATH}/install_component.sh",
                    self.workspace_name,
                    location,
                ],
                capture_output=True,
            )
            if process.returncode != 0:
                raise Exception(f"Failed to install component: {component}")

    def delete_resources(self):
        rmtree(self.workspace_path)
        rmtree(f"{VENVS_PATH}/{self.workspace_name}")


class VulkanComponentManager:
    def __init__(self, project_id: str, component_alias: str) -> None:
        self.project_id = project_id
        self.component_alias = component_alias

    @property
    def components_path(self) -> str:
        return f"{VULKAN_HOME}/components/{self.project_id}"

    def unpack_component(self, repository: bytes) -> str:
        return unpack_workspace(self.components_path, self.component_alias, repository)

    def delete_component(self):
        rmtree(f"{self.components_path}/{self.component_alias}")

import json
import os
import subprocess
from shutil import rmtree
from time import time

from vulkan_public.exceptions import (
    ConflictingDefinitionsError,
    DefinitionNotFoundException,
    InvalidDefinitionError,
)
from vulkan_public.spec.environment.workspace import VulkanCodeLocation
from vulkan_public.spec.environment.packing import unpack_workspace

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

    def get_policy_definition_settings(self) -> list[str]:
        return _get_policy_definition_settings(self.code_location, self.workspace_name)

    def create_venv(self) -> str:
        return _create_venv_for_workspace(self.venv_path, self.workspace_path)

    def install_components(self, required_components: list[str]):
        _install_components(
            self.workspace_name, self.components_path, required_components
        )

    def get_resolved_policy_settings(self):
        return _get_resolved_policy_settings(
            self.code_location, self.workspace_name, self.components_path
        )

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

    def load_component_definition(self):
        return _load_component_definition(self.components_path, self.component_alias)

    def delete_component(self):
        rmtree(f"{self.components_path}/{self.component_alias}")


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


def _get_policy_definition_settings(
    code_location: VulkanCodeLocation, workspace_name: str
):
    tmp_path = f"/tmp/{workspace_name}-{str(time())}.json"
    completed_process = subprocess.run(
        [
            f"{VENVS_PATH}/{workspace_name}/bin/python",
            f"{SCRIPTS_PATH}/get_policy_definition_settings.py",
            "--module_name",
            code_location.module_name,
            "--output_file",
            tmp_path,
        ],
        cwd=code_location.working_dir,
        capture_output=True,
    )
    exit_status = completed_process.returncode
    if exit_status == DefinitionNotFoundException().exit_status:
        raise DefinitionNotFoundException("Failed to load the PolicyDefinition")
    if exit_status == ConflictingDefinitionsError().exit_status:
        raise ConflictingDefinitionsError("Found multiple PolicyDefinitions")
    if exit_status == InvalidDefinitionError().exit_status:
        raise InvalidDefinitionError("PolicyDefinition is invalid")

    if exit_status != 0 or not os.path.exists(tmp_path):
        msg = f"Failed to get the required components: {completed_process.stderr}"
        raise Exception(msg)

    data = _load_and_remove(tmp_path)
    return data


def _get_resolved_policy_settings(
    code_location: VulkanCodeLocation, workspace_name: str, components_base_dir: str
):
    tmp_path = f"/tmp/{workspace_name}-{str(time())}.json"
    completed_process = subprocess.run(
        [
            f"{VENVS_PATH}/{workspace_name}/bin/python",
            f"{SCRIPTS_PATH}/get_resolved_policy_settings.py",
            "--module_name",
            code_location.module_name,
            "--components_base_dir",
            components_base_dir,
            "--output_file",
            tmp_path,
        ],
        cwd=code_location.working_dir,
        capture_output=True,
    )
    if completed_process.returncode != 0:
        msg = f"Failed to resolve policy: {completed_process.stderr}"
        raise Exception(msg)

    if not os.path.exists(tmp_path):
        msg = "Failed to resolve policy: Policy instance not found"
        raise Exception(msg)

    return _load_and_remove(tmp_path)


def _load_component_definition(components_path, component_alias):
    tmp_path = f"/tmp/{component_alias}-{str(time())}.json"
    completed_process = subprocess.run(
        [
            "bash",
            f"{SCRIPTS_PATH}/load_component_definition.sh",
            components_path,
            component_alias,
            tmp_path,
        ],
        capture_output=True,
    )
    exit_status = completed_process.returncode
    if exit_status == DefinitionNotFoundException().exit_status:
        raise DefinitionNotFoundException("Failed to load the ComponentDefinition")
    if exit_status == ConflictingDefinitionsError().exit_status:
        raise ConflictingDefinitionsError("Found multiple ComponentDefinitions")
    if exit_status == InvalidDefinitionError().exit_status:
        raise InvalidDefinitionError("ComponentDefinition is invalid")

    if exit_status != 0 or not os.path.exists(tmp_path):
        msg = f"Failed to load the ComponentDefinition: {completed_process.stderr}"
        raise Exception(msg)

    return _load_and_remove(tmp_path)


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


def _load_and_remove(file_path) -> dict:
    with open(file_path, "r") as fn:
        data = json.load(fn)
    os.remove(file_path)
    return data

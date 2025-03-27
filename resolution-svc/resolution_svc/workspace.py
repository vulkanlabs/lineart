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
from vulkan_public.spec.environment.packing import unpack_workspace
from vulkan_public.spec.environment.workspace import VulkanCodeLocation

from resolution_svc.config import VulkanConfig

VENVS_PATH = os.getenv("VULKAN_VENVS_PATH")
SCRIPTS_PATH = os.getenv("VULKAN_SCRIPTS_PATH")


class VulkanWorkspaceManager:
    def __init__(
        self, project_id: str, workspace_name: str, config: VulkanConfig
    ) -> None:
        self.project_id = project_id
        self.workspace_name = workspace_name
        self._code_location = None
        self.config = config

    @property
    def venv_path(self) -> str:
        return f"{self.config.venvs_path}/{self.workspace_name}"

    @property
    def workspace_base_path(self) -> str:
        return f"{self.config.home}/workspaces"

    @property
    def workspace_path(self) -> str:
        return f"{self.workspace_base_path}/{self.workspace_name}"

    @property
    def components_path(self) -> str:
        return f"{self.config.home}/components/{self.project_id}"

    @property
    def code_location(self) -> VulkanCodeLocation:
        if self._code_location is None:
            self._code_location = VulkanCodeLocation.from_workspace(self.workspace_path)
        return self._code_location

    def unpack_workspace(self, repository: bytes) -> str:
        workspace_path = unpack_workspace(
            self.workspace_base_path, self.workspace_name, repository
        )
        return workspace_path

    def get_policy_definition_settings(self) -> dict:
        return _get_policy_definition_settings(self.code_location, self.workspace_name)

    def create_venv(self) -> str:
        return _create_venv_for_workspace(self.venv_path, self.workspace_path)

    def get_resolved_policy_settings(self):
        return _get_resolved_policy_settings(
            self.code_location, self.workspace_name, self.components_path
        )

    def delete_resources(self):
        rmtree(self.workspace_path)
        rmtree(f"{self.config.venvs_path}/{self.workspace_name}")


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


def _load_and_remove(file_path) -> dict:
    with open(file_path, "r") as fn:
        data = json.load(fn)
    os.remove(file_path)
    return data

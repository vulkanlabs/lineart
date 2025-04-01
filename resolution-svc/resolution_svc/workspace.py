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

from resolution_svc.config import VulkanConfig
from resolution_svc.pyproject import get_pyproject, set_dependencies

VENVS_PATH = os.getenv("VULKAN_VENVS_PATH")
SCRIPTS_PATH = os.getenv("VULKAN_SCRIPTS_PATH")


class VulkanWorkspaceManager:
    def __init__(self, workspace_name: str, config: VulkanConfig) -> None:
        self.workspace_name = workspace_name
        self._code_location = None
        self.config = config

    @property
    def workspace_path(self) -> str:
        return f"{self.config.home}/workspaces/{self.workspace_name}"

    def create_workspace(self) -> str:
        completed_process = subprocess.run(
            [
                "bash",
                f"{SCRIPTS_PATH}/create_venv.sh",
                self.workspace_path,
            ],
            capture_output=True,
        )
        if completed_process.returncode != 0:
            msg = f"Failed to create virtual environment: {completed_process.stderr}"
            raise Exception(msg)
        return self.workspace_path

    def set_requirements(self, requirements: list[str]) -> None:
        if not os.path.exists(self.workspace_path):
            raise ValueError(f"Workspace does not exist: {self.workspace_path}")

        try:
            pyproject_path = f"{self.workspace_path}/pyproject.toml"
            set_dependencies(pyproject_path, requirements)
        except Exception as e:
            raise ValueError(f"Failed to set requirements: {e}")

    def get_requirements(self) -> list[str]:
        try:
            pyproject_path = f"{self.workspace_path}/pyproject.toml"
            pyproject = get_pyproject(pyproject_path)
            return pyproject["project"]["dependencies"]
        except Exception as e:
            raise ValueError(f"Failed to get requirements: {e}")

    def get_policy_definition_settings(self) -> dict:
        return _get_policy_definition_settings(self.code_location, self.workspace_name)

    def get_resolved_policy_settings(self):
        return _get_resolved_policy_settings(
            self.code_location, self.workspace_name, self.components_path
        )

    def delete_resources(self):
        rmtree(self.workspace_path)


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
    code_location: VulkanCodeLocation,
    workspace_name: str,
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

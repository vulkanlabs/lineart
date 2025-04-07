import os
import subprocess
from shutil import rmtree
import json

from vulkan.environment.loaders import SPEC_FILE_NAME

from .config import VulkanConfig
from .pyproject import get_pyproject, set_dependencies


class VulkanWorkspaceManager:
    def __init__(self, config: VulkanConfig, workspace_id: str) -> None:
        self.config = config
        self.workspace_path = os.path.join(config.workspaces_path, workspace_id)

    def create_workspace(self) -> None:
        completed_process = subprocess.run(
            [
                "bash",
                f"{self.config.scripts_path}/venv_create.sh",
                self.workspace_path,
            ],
            capture_output=True,
        )
        if completed_process.returncode != 0:
            msg = f"Failed to create virtual environment: {completed_process.stderr}"
            raise Exception(msg)

    def add_spec(self, spec: dict) -> None:
        if not os.path.exists(self.workspace_path):
            raise ValueError(f"Workspace does not exist: {self.workspace_path}")

        try:
            spec_path = f"{self.workspace_path}/{SPEC_FILE_NAME}"
            with open(spec_path, "w") as fp:
                json.dump(spec, fp)
        except Exception as e:
            raise ValueError(f"Failed to add spec: {e}")
    
    def set_requirements(self, requirements: list[str]) -> None:
        if not os.path.exists(self.workspace_path):
            raise ValueError(f"Workspace does not exist: {self.workspace_path}")

        try:
            pyproject_path = f"{self.workspace_path}/pyproject.toml"
            # TODO: is there a better way to do this?
            # We need to ensure vulkan-public is always in the requirements.
            reqs = list({"vulkan-public"}.union(set(requirements)))
            set_dependencies(pyproject_path, reqs)
            self._sync_requirements()
        except Exception as e:
            raise ValueError(f"Failed to set requirements: {e}")

    def get_requirements(self) -> list[str]:
        try:
            pyproject_path = f"{self.workspace_path}/pyproject.toml"
            pyproject = get_pyproject(pyproject_path)
            return pyproject["project"]["dependencies"]
        except Exception as e:
            raise ValueError(f"Failed to get requirements: {e}")

    def _sync_requirements(self) -> None:
        completed_process = subprocess.run(
            [
                "bash",
                f"{self.config.scripts_path}/venv_sync.sh",
                self.workspace_path,
            ],
            cwd=self.workspace_path,
            capture_output=True,
        )
        if completed_process.returncode != 0:
            msg = f"Failed to sync requirements: {completed_process.stderr}"
            raise Exception(msg)

    def delete_resources(self):
        rmtree(self.workspace_path)

import json
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from shutil import rmtree

from vulkan.runners.hatchet.workspace import HATCHET_ENTRYPOINT

from .config import VulkanConfig
from .pyproject import get_pyproject, set_dependencies

SPEC_FILE_NAME = Path("policy.json")
STATE_FILE_NAME = Path("state.json")
INIT_FILE_NAME = Path("__init__.py")


class HatchetWorkspaceManager:
    def __init__(self, config: VulkanConfig, workspace_id: str) -> None:
        self.config = config
        self._workspace_id = workspace_id
        self.workspace_path = os.path.join(config.workspaces_path, workspace_id)
        self.worker_task = None
        self.pool = ProcessPoolExecutor(max_workers=1)

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
            self._add_init_file(spec_path)
        except Exception as e:
            raise ValueError(f"Failed to add spec: {e}")

    def _add_init_file(self, spec_file_path: str) -> None:
        init_path = self.workspace_path / INIT_FILE_NAME
        with open(init_path, "w") as fp:
            fp.write(
                HATCHET_ENTRYPOINT.format(
                    spec_file_path=spec_file_path,
                    workflow_id=self._workspace_id,
                )
            )

    def set_requirements(self, requirements: list[str]) -> None:
        if not os.path.exists(self.workspace_path):
            raise ValueError(f"Workspace does not exist: {self.workspace_path}")

        try:
            pyproject_path = f"{self.workspace_path}/pyproject.toml"
            # We need to ensure vulkan is always in the requirements.
            reqs = list(DEFAULT_DEPENDENCIES.union(set(requirements)))
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

    def start_worker(self) -> None:
        if self.worker_task is not None:
            self.worker_task.terminate()
        task = self._start_worker_process()
        self.worker_task = task

    def _start_worker_process(self) -> subprocess.Popen:
        hatchet_task = subprocess.Popen(
            [
                f"{self.workspace_path}/.venv/bin/python",
                self.workspace_path / INIT_FILE_NAME,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return hatchet_task

    def stop_worker(self) -> tuple[bytes | None, bytes | None]:
        if self.worker_task is not None:
            stdout, stderr = self.worker_task.communicate(timeout=1)
            self.worker_task.terminate()
            self.worker_task = None
            return stdout, stderr

        return None, None


DEFAULT_DEPENDENCIES = {"vulkan[hatchet]"}

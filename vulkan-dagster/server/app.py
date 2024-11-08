import logging
import os
from typing import Annotated

from fastapi import Body, Depends, FastAPI
from vulkan.artifacts.gcs import GCSArtifactManager
from vulkan.dagster.workspace import DagsterWorkspaceManager

from .context import ExecutionContext
from .workspace import VulkanWorkspaceManager

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

VULKAN_HOME = os.getenv("VULKAN_HOME")
VENVS_PATH = os.getenv("VULKAN_VENVS_PATH")
SCRIPTS_PATH = os.getenv("VULKAN_SCRIPTS_PATH")


def get_artifact_manager():
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not GCP_PROJECT_ID or not GCP_BUCKET_NAME or not GOOGLE_APPLICATION_CREDENTIALS:
        raise ValueError("GCP configuration missing")

    return GCSArtifactManager(
        project_id=GCP_PROJECT_ID,
        bucket_name=GCP_BUCKET_NAME,
        token=GOOGLE_APPLICATION_CREDENTIALS,
    )


@app.post("/workspaces/create")
def create_workspace(
    name: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
    required_components: Annotated[list[str], Body()],
    artifacts: GCSArtifactManager = Depends(get_artifact_manager),
):
    """
    Create the dagster workspace and venv used to run a policy version.

    """
    logger.info(f"[{project_id}] Creating workspace: {name} (python_module)")
    vm = VulkanWorkspaceManager(project_id, name)

    with ExecutionContext(logger) as ctx:
        vm.unpack_workspace(artifacts, name)
        ctx.register_asset(vm.workspace_path)

        venv_path = vm.create_venv()
        ctx.register_asset(venv_path)

        vm.install_components(artifacts, required_components)

        dm = DagsterWorkspaceManager(VULKAN_HOME, vm.code_location)
        _ = dm.create_init_file(vm.components_path)
        dm.add_workspace_config(name, VENVS_PATH)
        logger.info(f"Successfully installed workspace: {name}")

    return {
        "workspace_path": vm.workspace_path,
    }


@app.post("/workspaces/delete")
def delete_workspace(
    name: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
):
    logger.info(f"[{project_id}] Deleting workspace: {name}")
    vm = VulkanWorkspaceManager(project_id, name)
    dm = DagsterWorkspaceManager(VULKAN_HOME, vm.code_location)

    with ExecutionContext(logger):
        dm.delete_resources(name)
        vm.delete_resources()

    logger.info(f"Successfully deleted workspace: {name}")
    return {"workspace_path": vm.workspace_path}

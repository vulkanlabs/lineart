import logging
import os
from typing import Annotated

from fastapi import Body, Depends, FastAPI, Response
from vulkan.dagster.workspace import DagsterWorkspaceManager

from .config import VulkanConfig, get_vulkan_config
from .context import ExecutionContext
from .workspace import VulkanWorkspaceManager

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


@app.post("/workspaces/{workspace_id}")
def create_workspace(
    workspace_id: str,
    spec: Annotated[dict, Body()],
    requirements: Annotated[list[str], Body()],
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
):
    logger.debug(f"Creating/updating workspace: {workspace_id}")
    vm = VulkanWorkspaceManager(vulkan_config, workspace_id)

    with ExecutionContext(logger) as ctx:
        if not os.path.exists(vm.workspace_path):
            vm.create_workspace()
            ctx.register_asset(vm.workspace_path)
            logger.debug(f"Created workspace at {vm.workspace_path}")

        if requirements:
            logger.debug(f"Adding requirements to workspace: {vm.workspace_path}")
            vm.set_requirements(requirements)
        if spec:
            logger.debug(f"Adding spec to workspace: {spec}")
            vm.add_spec(spec)

        dm = DagsterWorkspaceManager(vulkan_config.home, workspace_id, vm.workspace_path)
        dm.create_init_file()
        dm.add_workspace_config(workspace_id)
        logger.info(f"Successfully installed workspace: {workspace_id}")

    return {
        "workspace_path": vm.workspace_path,
    }


@app.get("/workspaces/{workspace_id}")
def get_workspace(
    workspace_id: str,
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
):
    vm = VulkanWorkspaceManager(vulkan_config, workspace_id)
    if not os.path.exists(vm.workspace_path):
        return Response(status_code=404)

    requirements = vm.get_requirements()
    return {"workspace_path": vm.workspace_path, "requirements": requirements}


@app.delete("/workspaces/{workspace_id}")
def delete_workspace(
    workspace_id: str,
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
):
    logger.info(f"Deleting workspace: {workspace_id}")
    vm = VulkanWorkspaceManager(vulkan_config, workspace_id)
    dm = DagsterWorkspaceManager(vulkan_config.home, vm.workspace_path)

    with ExecutionContext(logger):
        dm.delete_resources(workspace_id)
        vm.delete_resources()

    logger.info(f"Successfully deleted workspace: {workspace_id}")
    return {"workspace_path": vm.workspace_path}

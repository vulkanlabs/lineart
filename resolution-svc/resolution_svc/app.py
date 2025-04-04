import logging
import os
from typing import Annotated

from fastapi import Body, Depends, FastAPI, Response

from resolution_svc.config import VulkanConfig, get_vulkan_config
from resolution_svc.context import ExecutionContext
from resolution_svc.workspace import VulkanWorkspaceManager

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


@app.post("/workspaces/{workspace_id}")
def create_workspace(
    workspace_id: str,
    spec: Annotated[dict, Body()],
    requirements: Annotated[list[str], Body()],
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
):
    logger.debug(f"Creating workspace: {workspace_id}")
    vm = VulkanWorkspaceManager(workspace_id, vulkan_config)

    with ExecutionContext(logger) as ctx:
        if not os.path.exists(vm.workspace_path):
            logger.debug(f"Creating workspace: {vm.workspace_path}")
            vm.create_workspace()
            ctx.register_asset(vm.workspace_path)

        if requirements:
            logger.debug(f"Adding requirements to workspace: {vm.workspace_path}")
            vm.set_requirements(requirements)
        if spec:
            logger.debug(f"Adding spec to workspace: {spec}")

    logger.debug(f"Created workspace at: {vm.workspace_path}")
    return {"workspace_path": vm.workspace_path}


@app.get("/workspaces/{workspace_id}")
def get_workspace(
    workspace_id: str,
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
):
    vm = VulkanWorkspaceManager(workspace_id, vulkan_config)
    if not os.path.exists(vm.workspace_path):
        return Response(status_code=404)

    requirements = vm.get_requirements()
    return {"workspace_path": vm.workspace_path, "requirements": requirements}


@app.delete("/workspaces/{workspace_id}")
def delete_workspace(
    workspace_id: str,
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
):
    logger.debug(f"Deleting workspace: {workspace_id}")
    vm = VulkanWorkspaceManager(workspace_id, vulkan_config)
    with ExecutionContext(logger):
        vm.delete_resources()

    logger.debug(f"Successfully deleted workspace: {workspace_id}")
    return {"workspace_path": vm.workspace_path}

import logging
import os
from typing import Annotated

from fastapi import Body, Depends, FastAPI, Response

from resolution_svc.config import VulkanConfig, get_vulkan_config
from resolution_svc.context import ExecutionContext
from resolution_svc.workspace import VulkanWorkspaceManager

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


@app.post("/workspaces/{name}")
def create_workspace(
    name: str,
    spec: Annotated[dict, Body()],
    requirements: Annotated[list[str], Body()],
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
):
    logger.info(f"Creating workspace: {name}")
    vm = VulkanWorkspaceManager(name, vulkan_config)

    with ExecutionContext(logger) as ctx:
        workspace_path = vm.create_workspace()
        ctx.register_asset(workspace_path)

        if requirements:
            logger.info(f"Adding requirements to workspace: {vm.workspace_path}")
            vm.set_requirements(requirements)
        if spec:
            logger.info(f"Adding spec to workspace: {spec}")

    logger.info(f"Created workspace at: {vm.workspace_path}")
    return {"workspace_path": vm.workspace_path}


@app.get("/workspaces/{name}")
def get_workspace(
    name: str,
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
):
    vm = VulkanWorkspaceManager(name, vulkan_config)
    if not os.path.exists(vm.workspace_path):
        return Response(status_code=404)

    requirements = vm.get_requirements()
    return {"workspace_path": vm.workspace_path, "requirements": requirements}


@app.put("/workspaces/{name}")
def update_workspace(
    name: str,
    requirements: Annotated[list[str] | None, Body()] = None,
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
):
    logger.info(f"Creating workspace: {name}")
    vm = VulkanWorkspaceManager(name, vulkan_config)

    with ExecutionContext(logger):
        if not os.path.exists(vm.workspace_path):
            raise ValueError(f"Workspace does not exist: {vm.workspace_path}")

        if requirements:
            logger.info(f"Adding requirements to workspace: {vm.workspace_path}")
            vm.set_requirements(requirements)
    logger.info(f"Workspace updated: {vm.workspace_path}")

    return Response(status_code=200)


@app.delete("/workspaces/{name}")
def delete_workspace(
    name: str,
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
):
    logger.info(f"Deleting workspace: {name}")
    vm = VulkanWorkspaceManager(name, vulkan_config)
    with ExecutionContext(logger):
        vm.delete_resources()

    logger.info(f"Successfully deleted workspace: {name}")
    return {"workspace_path": vm.workspace_path}

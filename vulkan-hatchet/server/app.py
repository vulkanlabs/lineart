import logging
import os
from typing import Annotated

from fastapi import Body, Depends, FastAPI, Response

from .config import VulkanConfig, get_vulkan_config
from .context import ExecutionContext
from .workspace import HatchetWorkspaceManager

app = FastAPI(title="Vulkan Hatchet Server")

logging.basicConfig(format="[%(name)s] %(levelname)s - %(asctime)s - %(message)s")
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
    vm = HatchetWorkspaceManager(vulkan_config, workspace_id)

    with ExecutionContext(logger) as ctx:
        if not os.path.exists(vm.workspace_path):
            vm.create_workspace()
            ctx.register_asset(vm.workspace_path)
            logger.debug(f"Created workspace at {vm.workspace_path}")

        if requirements:
            vm.set_requirements(requirements)
            logger.debug(f"Added requirements to workspace: {vm.workspace_path}")

        if spec:
            vm.add_spec(spec)
            logger.debug(f"Added spec to workspace: {spec}")

        stdout, stderr = vm.stop_worker()
        if stdout:
            logger.debug(f"[{workspace_id}] Worker stdout: {stdout.decode()}")
        if stderr:
            logger.error(f"[{workspace_id}] Worker stderr: {stderr.decode()}")
        logger.info(f"Starting worker for workspace: {workspace_id}")
        vm.start_worker()
        logger.info(f"Successfully started worker for workspace: {workspace_id}")

    return {
        "workspace_path": vm.workspace_path,
    }


@app.get("/workspaces/{workspace_id}")
def get_workspace(
    workspace_id: str,
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
):
    vm = HatchetWorkspaceManager(vulkan_config, workspace_id)
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
    vm = HatchetWorkspaceManager(vulkan_config, workspace_id)

    with ExecutionContext(logger):
        vm.delete_resources()

    logger.info(f"Successfully deleted workspace: {workspace_id}")
    return {"workspace_path": vm.workspace_path}

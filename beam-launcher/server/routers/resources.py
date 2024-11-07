import base64
import logging
import os
from typing import Annotated

from fastapi import APIRouter, Body
from vulkan_public.exceptions import ConflictingDefinitionsError

from server.context import ExecutionContext
from server.workspace import VulkanComponentManager, VulkanWorkspaceManager

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


router = APIRouter(
    prefix="/resources",
    tags=["resources"],
    responses={404: {"description": "Not found"}},
)


@router.post("/workspaces")
def create_workspace(
    project_id: Annotated[str, Body()],
    policy_version_id: Annotated[str, Body()],
    repository: Annotated[str, Body()],
    required_components: Annotated[list[str], Body()],
):
    logger.info(f"[{project_id}] Creating workspace: {policy_version_id} (python_module)")
    vm = VulkanWorkspaceManager(project_id, policy_version_id)

    with ExecutionContext(logger) as ctx:
        repository = base64.b64decode(repository)
        workspace_path = vm.unpack_workspace(repository)
        ctx.register_asset(workspace_path)

        venv_path = vm.create_venv()
        ctx.register_asset(venv_path)

        vm.install_components(required_components)

    logger.info(f"Created workspace at: {workspace_path}")
    return {"workspace_path": workspace_path}


@router.delete("/workspaces")
def delete_workspace(
    policy_version_id: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
):
    logger.info(f"[{project_id}] Deleting workspace: {policy_version_id}")
    vm = VulkanWorkspaceManager(project_id, policy_version_id)

    with ExecutionContext(logger):
        vm.delete_resources()

    logger.info(f"Successfully deleted workspace: {policy_version_id}")
    return {"workspace_path": vm.workspace_path}


@router.post("/components")
def create_component(
    alias: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
    repository: Annotated[str, Body()],
):
    logger.info(f"[{project_id}] Creating component version: {alias}")
    cm = VulkanComponentManager(project_id, alias)

    with ExecutionContext(logger) as ctx:
        if os.path.exists(os.path.join(cm.components_path, alias)):
            raise ConflictingDefinitionsError("Component version already exists")

        repository = base64.b64decode(repository)
        component_path = cm.unpack_component(repository)
        logger.info(f"Unpacked and stored component spec at: {component_path}")
        ctx.register_asset(component_path)

    return {"component_path": component_path}


@router.delete("/components")
def delete_component(
    alias: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
):
    logger.info(f"Deleting component version: {alias}")
    cm = VulkanComponentManager(project_id, alias)

    with ExecutionContext(logger):
        cm.delete_component()

    logger.info(f"Successfully deleted component version: {alias}")
    return {"component_alias": alias}

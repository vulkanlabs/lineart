import base64
import logging
import os
from typing import Annotated

from fastapi import Body, FastAPI
from vulkan.dagster.workspace import DagsterWorkspaceManager
from vulkan_public.exceptions import ConflictingDefinitionsError

from . import schemas
from .context import ExecutionContext
from .workspace import VulkanComponentManager, VulkanWorkspaceManager

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

VULKAN_HOME = os.getenv("VULKAN_HOME")
VENVS_PATH = os.getenv("VULKAN_VENVS_PATH")
SCRIPTS_PATH = os.getenv("VULKAN_SCRIPTS_PATH")


@app.post("/workspaces/create")
def create_workspace(
    name: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
    repository: Annotated[str, Body()],
):
    """
    Create the dagster workspace and venv used to run a policy version.

    """
    logger.info(f"[{project_id}] Creating workspace: {name} (python_module)")
    vm = VulkanWorkspaceManager(project_id, name)

    with ExecutionContext(logger) as ctx:
        repository = base64.b64decode(repository)
        workspace_path = vm.unpack_workspace(repository)
        ctx.register_asset(workspace_path)

        venv_path = vm.create_venv()
        ctx.register_asset(venv_path)

        policy_definition_settings = vm.get_policy_definition_settings()

    logger.info(f"Created workspace at: {workspace_path}")

    return {
        "policy_definition_settings": policy_definition_settings,
        "workspace_path": workspace_path,
    }


@app.post("/workspaces/install")
def install_workspace(
    name: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
    required_components: Annotated[list[str], Body()],
):
    """
    Install components, resolve policy definition and add workspace to Dagster.

    """
    logger.info(f"[{project_id}] Installing workspace: {name}")
    vm = VulkanWorkspaceManager(project_id, name)
    dm = DagsterWorkspaceManager(VULKAN_HOME, vm.code_location)

    with ExecutionContext(logger):
        vm.install_components(required_components)
        _ = dm.create_init_file(vm.components_path)
        node_definitions = vm.get_node_definitions()

    dm.add_workspace_config(name, VENVS_PATH)
    logger.info(f"Successfully installed workspace: {name}")

    return {"graph": node_definitions}


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


@app.post("/components", response_model=schemas.ComponentConfig)
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

        definition = cm.load_component_definition()
        logger.info(f"Loaded component definition: {definition}")

    return definition


@app.post("/components/delete")
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

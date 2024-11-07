import base64
import logging
import os
from typing import Annotated

from fastapi import Body, FastAPI, Depends
from vulkan_public.exceptions import ConflictingDefinitionsError

from . import schemas
from .context import ExecutionContext
from .workspace import (
    GCSWorkspaceManager,
    VulkanComponentManager,
    VulkanWorkspaceManager,
)

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

VULKAN_HOME = os.getenv("VULKAN_HOME")
VENVS_PATH = os.getenv("VULKAN_VENVS_PATH")
SCRIPTS_PATH = os.getenv("VULKAN_SCRIPTS_PATH")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")


def get_gcs_manager():
    return GCSWorkspaceManager(GCP_PROJECT_ID, GCP_BUCKET_NAME)


@app.post("/workspaces/create")
def create_workspace(
    name: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
    repository: Annotated[str, Body()],
    gcs: GCSWorkspaceManager = Depends(get_gcs_manager),
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
        required_components = policy_definition_settings["required_components"]
        # TODO Check components are available

        logger.info(f"[{project_id}] Installing workspace: {name}")
        vm.install_components(required_components)
        settings = vm.get_resolved_policy_settings()
        logger.info(f"[{project_id}] Successfully installed workspace: {name}")
        # TODO: maybe share with dagster server
        # vm.render_dockerfile(required_components)
        gcs.post(project_id, "policy", name, repository)

    logger.info(f"Created workspace at: {workspace_path}")
    return {
        "policy_definition_settings": policy_definition_settings,
        "workspace_path": workspace_path,
        "graph_definition": settings["nodes"],
        "data_sources": settings["data_sources"],
    }


@app.post("/workspaces/delete")
def delete_workspace(
    name: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
):
    logger.info(f"[{project_id}] Deleting workspace: {name}")
    vm = VulkanWorkspaceManager(project_id, name)
    with ExecutionContext(logger):
        vm.delete_resources()

    logger.info(f"Successfully deleted workspace: {name}")

    return {"workspace_path": vm.workspace_path}


@app.post("/components", response_model=schemas.ComponentConfig)
def create_component(
    alias: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
    repository: Annotated[str, Body()],
    gcs: GCSWorkspaceManager = Depends(get_gcs_manager),
):
    logger.info(f"[{project_id}] Creating component version: {alias}")
    cm = VulkanComponentManager(project_id, alias,)

    with ExecutionContext(logger) as ctx:
        if os.path.exists(os.path.join(cm.components_path, alias)):
            raise ConflictingDefinitionsError("Component version already exists")

        repository = base64.b64decode(repository)
        component_path = cm.unpack_component(repository)
        logger.info(f"Unpacked and stored component spec at: {component_path}")
        ctx.register_asset(component_path)

        definition = cm.load_component_definition()
        logger.info(f"Loaded component definition: {definition}")
        gcs.post(project_id, "component", alias, repository)        

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

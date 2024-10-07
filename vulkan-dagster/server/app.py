import base64
import json
import logging
import os
import subprocess
from shutil import rmtree
from time import time
from typing import Annotated

from fastapi import Body, FastAPI, Form
from vulkan.dagster.workspace import DagsterWorkspaceManager
from vulkan.environment.workspace import VulkanCodeLocation
from vulkan_public.exceptions import (
    ConflictingDefinitionsError,
    DefinitionNotFoundException,
    InvalidDefinitionError,
)
from vulkan_public.spec.environment.packing import unpack_workspace

from . import schemas
from .context import ExecutionContext

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
    repository = base64.b64decode(repository)
    logger.info(f"[{project_id}] Creating workspace: {name} (python_module)")

    with ExecutionContext(logger) as ctx:
        # TODO: handle resources below through VulkanWorkspaceManager
        workspace_path = unpack_workspace(f"{VULKAN_HOME}/workspaces", name, repository)
        ctx.register_asset(workspace_path)

        venv_path = _create_venv_for_workspace(name, workspace_path)
        ctx.register_asset(venv_path)

        code_location = VulkanCodeLocation.from_workspace(workspace_path)
        required_components = _get_required_components(code_location, name)

    logger.info(f"Created workspace at: {workspace_path}")

    return {
        "required_components": required_components,
        "workspace_path": workspace_path,
    }


@app.post("/workspaces/install")
def install_workspace(
    name: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
    workspace_path: Annotated[str, Body()],
    required_components: Annotated[list[str], Body()],
):
    """
    Install components, resolve policy definition and add workspace to Dagster.

    """
    logger.info(f"[{project_id}] Installing workspace: {name}")
    code_location = VulkanCodeLocation.from_workspace(workspace_path)
    dw = DagsterWorkspaceManager(
        project_id=project_id, base_dir=VULKAN_HOME, code_location=code_location
    )

    with ExecutionContext(logger):
        # TODO: handle resources below through VulkanWorkspaceManager
        components_base_dir = _get_components_base_dir(project_id)
        _install_components(name, components_base_dir, required_components)
        # -----

        # TODO: rename _resolve_policy -> get_node_definitions
        resolved_graph = _resolve_policy(code_location, name, components_base_dir)
        _ = dw.create_init_file(components_base_dir)

    dw.add_workspace_config(name)
    logger.info(f"Successfully installed workspace: {name}")

    return {"graph": resolved_graph}


@app.post("/workspaces/delete")
def delete_workspace(
    name: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
    workspace_path: Annotated[str, Body()],
):
    logger.info(f"[{project_id}] Deleting workspace: {name}")

    with ExecutionContext(logger):
        code_location = VulkanCodeLocation.from_workspace(workspace_path)
        dw = DagsterWorkspaceManager(
            project_id=project_id, base_dir=VULKAN_HOME, code_location=code_location
        )
        dw.delete_resources(name)

        # TODO: handle these resources through VulkanWorkspaceManager
        rmtree(workspace_path)
        rmtree(f"{VENVS_PATH}/{name}")

    logger.info(f"Successfully deleted workspace: {name}")

    return {"workspace_path": workspace_path}


# TODO: We need to segregate workspaces to enable users to
# create components without colliding with other users' components.
@app.post("/components", response_model=schemas.ComponentConfig)
def create_component(
    alias: Annotated[str, Form()],
    project_id: Annotated[str, Form()],
    repository: Annotated[str, Form()],
):
    base_dir = _get_components_base_dir(project_id)
    logger.info(f"[{project_id}] Creating component version: {alias}")

    with ExecutionContext(logger) as ctx:
        if os.path.exists(os.path.join(base_dir, alias)):
            raise ConflictingDefinitionsError("Component version already exists")

        repository = base64.b64decode(repository)
        component_path = unpack_workspace(base_dir, alias, repository)
        logger.info(f"Unpacked and stored component spec at: {component_path}")
        ctx.register_asset(component_path)

        definition = _load_component_definition(base_dir, alias)
        logger.info(f"Loaded component definition: {definition}")

    return definition


@app.post("/components/delete")
def delete_component(
    alias: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
):
    base_dir = _get_components_base_dir(project_id)
    logger.info(f"Deleting component version: {alias}")

    with ExecutionContext(logger):
        rmtree(os.path.join(base_dir, alias))

    logger.info(f"Successfully deleted component version: {alias}")

    return {"component_alias": alias}


def _create_venv_for_workspace(workspace_name, workspace_path):
    venv_path = f"{VENVS_PATH}/{workspace_name}"
    completed_process = subprocess.run(
        [
            "bash",
            f"{SCRIPTS_PATH}/create_venv.sh",
            venv_path,
            workspace_path,
        ],
        capture_output=True,
    )
    if completed_process.returncode != 0:
        msg = f"Failed to create virtual environment: {completed_process.stderr}"
        raise Exception(msg)
    return venv_path


def _get_required_components(code_location: VulkanCodeLocation, workspace_name: str):
    tmp_path = f"/tmp/{workspace_name}-{str(time())}.json"
    completed_process = subprocess.run(
        [
            f"{VENVS_PATH}/{workspace_name}/bin/python",
            f"{SCRIPTS_PATH}/get_required_components.py",
            "--file_location",
            code_location.entrypoint,
            "--output_file",
            tmp_path,
        ],
        cwd=code_location.working_dir,
        capture_output=True,
    )
    exit_status = completed_process.returncode
    if exit_status == DefinitionNotFoundException().exit_status:
        raise DefinitionNotFoundException("Failed to load the PolicyDefinition")
    if exit_status == ConflictingDefinitionsError().exit_status:
        raise ConflictingDefinitionsError("Found multiple PolicyDefinitions")
    if exit_status == InvalidDefinitionError().exit_status:
        raise InvalidDefinitionError("PolicyDefinition is invalid")

    if exit_status != 0 or not os.path.exists(tmp_path):
        msg = f"Failed to get the required components: {completed_process.stderr}"
        raise Exception(msg)

    data = _load_and_remove(tmp_path)
    return data["required_components"]


def _resolve_policy(
    code_location: VulkanCodeLocation, workspace_name: str, components_base_dir: str
):
    tmp_path = f"/tmp/{workspace_name}-{str(time())}.json"
    completed_process = subprocess.run(
        [
            f"{VENVS_PATH}/{workspace_name}/bin/python",
            f"{SCRIPTS_PATH}/resolve_policy.py",
            "--file_location",
            code_location.entrypoint,
            "--components_base_dir",
            components_base_dir,
            "--output_file",
            tmp_path,
        ],
        cwd=code_location.working_dir,
        capture_output=True,
    )
    if completed_process.returncode != 0:
        msg = f"Failed to resolve policy: {completed_process.stderr}"
        raise Exception(msg)

    if not os.path.exists(tmp_path):
        msg = "Failed to resolve policy: Policy instance not found"
        raise Exception(msg)

    return _load_and_remove(tmp_path)


def _load_component_definition(components_base_dir, component_alias):
    tmp_path = f"/tmp/{component_alias}-{str(time())}.json"
    completed_process = subprocess.run(
        [
            "bash",
            f"{SCRIPTS_PATH}/load_component_definition.sh",
            components_base_dir,
            component_alias,
            tmp_path,
        ],
        capture_output=True,
    )
    exit_status = completed_process.returncode
    if exit_status == DefinitionNotFoundException().exit_status:
        raise DefinitionNotFoundException("Failed to load the ComponentDefinition")
    if exit_status == ConflictingDefinitionsError().exit_status:
        raise ConflictingDefinitionsError("Found multiple ComponentDefinitions")
    if exit_status == InvalidDefinitionError().exit_status:
        raise InvalidDefinitionError("ComponentDefinition is invalid")

    if exit_status != 0 or not os.path.exists(tmp_path):
        msg = f"Failed to load the ComponentDefinition: {completed_process.stderr}"
        raise Exception(msg)

    return _load_and_remove(tmp_path)


def _install_components(workspace_name, components_base_dir, required_components):
    logger.info(f"Installing components for workspace: {workspace_name}")
    for component_alias in required_components:
        component_path = os.path.join(components_base_dir, component_alias)
        completed_process = subprocess.run(
            [
                "bash",
                f"{SCRIPTS_PATH}/install_component.sh",
                workspace_name,
                component_path,
            ],
            capture_output=True,
        )
        if completed_process.returncode != 0:
            raise Exception(f"Failed to install component: {component_alias}")


def _get_components_base_dir(project_id: str) -> str:
    return f"{VULKAN_HOME}/components/{project_id}"


def _load_and_remove(file_path):
    with open(file_path, "r") as fn:
        data = json.load(fn)
    os.remove(file_path)
    return data

import base64
import json
import logging
import os
import subprocess
from dataclasses import dataclass
from shutil import rmtree
from time import time
from typing import Annotated

import yaml
from fastapi import Body, FastAPI, Form
from vulkan.dagster.workspace import add_workspace_config, remove_workspace_config
from vulkan.exceptions import (
    ConflictingDefinitionsError,
    DefinitionNotFoundException,
    InvalidDefinitionError,
)
from vulkan.spec.environment.config import VulkanWorkspaceConfig, get_working_directory
from vulkan.spec.environment.packing import find_package_entrypoint, unpack_workspace

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
    repository: Annotated[str, Body()],
):
    """
    Create the dagster workspace and venv used to run a policy version.

    """
    repository = base64.b64decode(repository)
    logger.info(f"Creating workspace: {name} (python_module)")

    with ExecutionContext(logger) as ctx:
        workspace_path = unpack_workspace(f"{VULKAN_HOME}/workspaces", name, repository)
        ctx.register_asset(workspace_path)

        venv_path = _create_venv_for_workspace(name, workspace_path)
        ctx.register_asset(venv_path)

        code_location = _get_code_location(workspace_path)
        required_components = _get_required_components(
            name, code_location.entrypoint, workspace_path
        )

    logger.info(f"Created workspace at: {workspace_path}")

    return {
        "required_components": required_components,
        "workspace_path": workspace_path,
    }


@app.post("/workspaces/install")
def install_workspace(
    name: Annotated[str, Body()],
    workspace_path: Annotated[str, Body()],
    required_components: Annotated[list[str], Body()],
):
    """
    Install components, resolve policy definition and add workspace to Dagster.

    """
    logger.info(f"Installing workspace: {name}")

    with ExecutionContext(logger):
        _install_components(name, required_components)

        code_location = _get_code_location(workspace_path)
        resolved_graph = _resolve_policy(name, code_location.entrypoint, workspace_path)

        definition_path = _get_definition_path(code_location)
        _ = _create_init_file(code_location.entrypoint, definition_path)

    add_workspace_config(
        VULKAN_HOME,
        name,
        definition_path,
        code_location.module_name,
    )
    logger.info(f"Successfully installed workspace: {name}")

    return {"graph": resolved_graph}


@app.post("/workspaces/delete")
def delete_workspace(
    name: Annotated[str, Body()],
    workspace_path: Annotated[str, Body()],
):
    logger.info(f"Deleting workspace: {name}")

    with ExecutionContext(logger):
        code_location = _get_code_location(workspace_path)
        definition_path = _get_definition_path(code_location)
        rmtree(definition_path)
        rmtree(workspace_path)
        rmtree(f"{VENVS_PATH}/{name}")
        remove_workspace_config(VULKAN_HOME, name)

    logger.info(f"Successfully deleted workspace: {name}")

    return {"workspace_path": workspace_path}


# TODO: We need to segregate workspaces to enable users to
# create components without colliding with other users' components.
@app.post("/components", response_model=schemas.ComponentConfig)
def create_component(
    alias: Annotated[str, Form()],
    repository: Annotated[str, Form()],
):
    base_dir = f"{VULKAN_HOME}/components"
    logger.info(f"Creating component version: {alias}")

    with ExecutionContext(logger) as ctx:
        if os.path.exists(os.path.join(base_dir, alias)):
            raise ConflictingDefinitionsError("Component version already exists")

        repository = base64.b64decode(repository)
        component_path = unpack_workspace(base_dir, alias, repository)
        logger.info(f"Unpacked and stored component spec at: {component_path}")
        ctx.register_asset(component_path)

        definition = _load_component_definition(alias)
        logger.info(f"Loaded component definition: {definition}")

    return definition


@app.post("/components/delete")
def delete_component(
    alias: Annotated[str, Body(embed=True)],
):
    base_dir = f"{VULKAN_HOME}/components"
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


def _get_required_components(workspace_name, code_entrypoint, workspace_path):
    tmp_path = f"/tmp/{workspace_name}-{str(time())}.json"
    completed_process = subprocess.run(
        [
            f"{VENVS_PATH}/{workspace_name}/bin/python",
            f"{SCRIPTS_PATH}/get_required_components.py",
            "--file_location",
            code_entrypoint,
            "--output_file",
            tmp_path,
        ],
        cwd=workspace_path,
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


def _resolve_policy(workspace_name, code_entrypoint, workspace_path):
    tmp_path = f"/tmp/{workspace_name}-{str(time())}.json"
    completed_process = subprocess.run(
        [
            f"{VENVS_PATH}/{workspace_name}/bin/python",
            f"{SCRIPTS_PATH}/resolve_policy.py",
            "--file_location",
            code_entrypoint,
            "--components_base_dir",
            f"{VULKAN_HOME}/components",
            "--output_file",
            tmp_path,
        ],
        cwd=workspace_path,
        capture_output=True,
    )
    if completed_process.returncode != 0:
        msg = f"Failed to resolve policy: {completed_process.stderr}"
        raise Exception(msg)

    if not os.path.exists(tmp_path):
        msg = "Failed to resolve policy: Policy instance not found"
        raise Exception(msg)

    return _load_and_remove(tmp_path)


def _load_component_definition(component_alias):
    tmp_path = f"/tmp/{component_alias}-{str(time())}.json"
    completed_process = subprocess.run(
        [
            "bash",
            f"{SCRIPTS_PATH}/load_component_definition.sh",
            SCRIPTS_PATH,
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


def _install_components(workspace_name, required_components):
    logger.info(f"Installing components for workspace: {workspace_name}")
    for component in required_components:
        completed_process = subprocess.run(
            [
                "bash",
                f"{SCRIPTS_PATH}/install_component.sh",
                component,
                workspace_name,
            ],
            capture_output=True,
        )
        if completed_process.returncode != 0:
            raise Exception(f"Failed to install component: {component}")


@dataclass
class VulkanCodeLocation:
    working_dir: str
    module_name: str
    entrypoint: str


def _get_code_location(workspace_path):
    config = VulkanWorkspaceConfig.from_workspace(workspace_path)
    working_dir, module_name = get_working_directory(config, workspace_path)
    code_path = os.path.join(working_dir, module_name)
    entrypoint = find_package_entrypoint(code_path)
    return VulkanCodeLocation(
        working_dir=working_dir,
        module_name=module_name,
        entrypoint=entrypoint,
    )


def _create_init_file(code_entrypoint, working_dir) -> str:
    os.makedirs(working_dir, exist_ok=True)
    init_path = os.path.join(working_dir, "__init__.py")
    components_base_dir = os.path.join(VULKAN_HOME, "components")

    init_contents = f"""
from vulkan.dagster.workspace import make_workspace_definition
                 
definitions = make_workspace_definition("{code_entrypoint}", "{components_base_dir}")
"""
    with open(init_path, "w") as fp:
        fp.write(init_contents)

    return init_path


def _get_definition_path(code_location):
    # TODO: we're replacing /workspaces with /definitions as a convenience.
    # We could have a more thorough definition of where the defs are stored.
    return code_location.working_dir.replace("/workspaces", "/definitions", 1)


def _load_and_remove(file_path):
    with open(file_path, "r") as fn:
        data = json.load(fn)
    os.remove(file_path)
    return data

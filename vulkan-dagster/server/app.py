import base64
import json
import logging
import os
import subprocess
from shutil import rmtree
from typing import Annotated
from time import time

from fastapi import Body, FastAPI, Form, HTTPException
from vulkan.dagster.workspace import add_workspace_config
from vulkan.environment.config import VulkanWorkspaceConfig, get_working_directory
from vulkan.environment.packing import find_package_entrypoint, unpack_workspace

from . import schemas

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

VULKAN_HOME = os.getenv("VULKAN_HOME")
VENVS_PATH = os.getenv("VULKAN_VENVS_PATH")
SCRIPTS_PATH = os.getenv("VULKAN_SCRIPTS_PATH")


@app.post("/workspaces")
def create_workspace(
    name: Annotated[str, Body()],
    repository: Annotated[str, Body()],
):
    """
    Create the dagster workspace and venv used to run a policy version.


    """
    repository = base64.b64decode(repository)
    logger.info(f"Creating workspace: {name} (python_module)")

    try:
        workspace_path = unpack_workspace(
            f"{VULKAN_HOME}/workspaces", name, repository
        )

        config = VulkanWorkspaceConfig.from_workspace(workspace_path)
        working_dir, module_name = get_working_directory(config, workspace_path)
        code_path = os.path.join(working_dir, module_name)
        code_entrypoint = find_package_entrypoint(code_path)

        # TODO: we're replacing /workspaces with /definitions as a convenience.
        # We could have a more thorough definition of where the defs are stored.
        definition_path = working_dir.replace("/workspaces", "/definitions", 1)
        _ = _create_init_file(code_entrypoint, definition_path)

        _create_venv_for_workspace(name, workspace_path)
        required_components = _get_required_components(
            name, code_entrypoint, workspace_path
        )
        _install_components(name, required_components)

        resolved_graph = _resolve_policy(name, code_entrypoint, workspace_path)

    except Exception as e:
        logger.error(f"Failed create workspace: {e}")
        raise HTTPException(status_code=500, detail=e)

    add_workspace_config(
        VULKAN_HOME,
        name,
        definition_path,
        module_name,
    )
    logger.info(f"Created workspace at: {workspace_path}")

    return {
        "graph": resolved_graph,
        "required_components": required_components,
        "workspace_path": workspace_path,
    }


@app.post("/components", response_model=schemas.ComponentConfig)
def create_component(
    alias: Annotated[str, Form()],
    repository: Annotated[str, Form()],
):
    base_dir = f"{VULKAN_HOME}/components"
    component_path = os.path.join(base_dir, alias)
    if os.path.exists(component_path):
        raise HTTPException(
            status_code=409,
            detail="Component already exists",
        )

    logger.info(f"Creating component: {alias}")
    repository = base64.b64decode(repository)

    try:
        component_path = unpack_workspace(base_dir, alias, repository)
        definition = _load_component_definition(alias)
        logger.info(f"Loaded component definition: {definition}")
    except Exception as e:
        logger.error(f"Failed create component: {e}")
        if os.path.exists(component_path):
            rmtree(component_path)

        raise HTTPException(
            status_code=500,
            detail="Failed to create component",
        )

    logger.info(f"Created component at: {component_path}")
    return definition


def _create_venv_for_workspace(workspace_name, workspace_path):
    completed_process = subprocess.run(
        [
            "bash",
            f"{SCRIPTS_PATH}/create_venv.sh",
            workspace_name,
            workspace_path,
        ],
        capture_output=True,
    )
    if completed_process.returncode != 0:
        msg = f"Failed to create virtual environment: {completed_process.stderr}"
        raise Exception(msg)


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
    if completed_process.returncode != 0 or not os.path.exists(tmp_path):
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
    if completed_process.returncode != 0:
        msg = f"Failed to load component: {completed_process.stderr}"
        raise Exception(msg)

    if not os.path.exists(tmp_path):
        msg = "Failed to load component: ComponentDefinition instance not found"
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


def _load_and_remove(file_path):
    with open(file_path, "r") as fn:
        data = json.load(fn)
    os.remove(file_path)
    return data
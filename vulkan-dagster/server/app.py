import base64
import json
import logging
import os
import subprocess
from shutil import rmtree
from typing import Annotated

import yaml
from fastapi import Body, FastAPI, Form, HTTPException
from vulkan.dagster.workspace import add_workspace_config
from vulkan.environment.config import PackagingMode, VulkanWorkspaceConfig
from vulkan.environment.packing import find_package_entrypoint, unpack_workspace

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

DAGSTER_HOME = os.getenv("DAGSTER_HOME")
VENVS_PATH = os.getenv("VULKAN_VENVS_PATH")
SCRIPTS_PATH = os.getenv("VULKAN_SCRIPTS_PATH")


@app.post("/workspaces")
def create_workspace(
    name: Annotated[str, Body()],
    repository: Annotated[str, Body()],
    required_components: Annotated[list[str] | None, Body()] = None,
):
    """
    Create the dagster workspace and venv used to run a policy version.


    """
    repository = base64.b64decode(repository)
    logger.info(f"Creating workspace: {name} (python_module)")

    try:
        workspace_path = unpack_workspace(
            f"{DAGSTER_HOME}/workspaces", name, repository
        )

        completed_process = subprocess.run(
            [
                "bash",
                f"{SCRIPTS_PATH}/create_venv.sh",
                name,
                workspace_path,
                " ".join(required_components) if required_components else "",
            ],
            capture_output=True,
        )
        if completed_process.returncode != 0:
            msg = f"Failed to create virtual environment: {completed_process.stderr}"
            raise Exception(msg)

        config_path = os.path.join(workspace_path, "vulkan.yaml")
        with open(config_path, "r") as fn:
            config_data = yaml.safe_load(fn)
        config = VulkanWorkspaceConfig.from_dict(config_data)

        working_dir, module_name = _get_working_directory(config, workspace_path)
        code_path = os.path.join(working_dir, module_name)
        code_entrypoint = find_package_entrypoint(code_path)

        # TODO: we're replacing /workspaces with /definitions as a convenience.
        # We could have a more thorough definition of where the defs are stored.
        definition_path = working_dir.replace("/workspaces", "/definitions", 1)
        add_workspace_config(
            DAGSTER_HOME,
            name,
            definition_path,
            module_name,
        )
        # TODO: install the library AND create an init in the definitions folder
        _ = _create_init_file(code_entrypoint, definition_path)

        tmp_path = "/tmp/nodes.json"
        completed_process = subprocess.run(
            [
                f"{VENVS_PATH}/{name}/bin/python",
                f"{SCRIPTS_PATH}/extract_node_definitions.py",
                "--file_location",
                code_entrypoint,
                "--output_file",
                tmp_path,
            ],
            cwd=workspace_path,
            capture_output=True,
        )
        if completed_process.returncode != 0:
            msg = f"Failed to create virtual environment: {completed_process.stderr}"
            raise Exception(msg)

        if not os.path.exists(tmp_path):
            msg = "Failed to create virtual environment: Policy instance not found"
            raise Exception(msg)

        with open(tmp_path, "r") as fn:
            nodes = json.load(fn)
        os.remove(tmp_path)

    except Exception as e:
        logger.error(f"Failed create workspace: {e}")
        raise HTTPException(status_code=500, detail=e)

    logger.info(f"Created workspace at: {workspace_path}")
    return {"workspace_path": workspace_path, "graph": nodes}


@app.post("/components")
def create_component(
    alias: Annotated[str, Form()],
    repository: Annotated[str, Form()],
):
    base_dir = f"{DAGSTER_HOME}/components"
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
    except Exception as e:
        logger.error(f"Failed create component: {e}")
        if os.path.exists(component_path):
            rmtree(component_path)

        raise HTTPException(
            status_code=500,
            detail="Failed to create component",
        )

    logger.info(f"Created component at: {component_path}")
    return {"status": "success"}


def _install_components(name, dependencies):
    logger.info(f"Installing components for workspace: {name}")
    for dependency in dependencies:
        result = subprocess.run(
            [
                "bash",
                f"{SCRIPTS_PATH}/install_component.sh",
                dependency,
                name,
            ],
            capture_output=True,
        )
        if result.returncode != 0:
            raise Exception(f"Failed to install dependency: {dependency}")


def _get_working_directory(
    config: VulkanWorkspaceConfig,
    workspace_path: str,
) -> tuple[str, str]:
    if config.packaging.mode == PackagingMode.PYTHON_PACKAGE:
        working_directory = workspace_path
        module_name = config.packaging.entrypoint
    else:
        raise ValueError(f"Unsupported packaging mode: {config.packaging.mode}")

    return working_directory, module_name


def _create_init_file(code_entrypoint, working_dir) -> str:
    os.makedirs(working_dir, exist_ok=True)
    init_path = os.path.join(working_dir, "__init__.py")
    components_base_dir = os.path.join(DAGSTER_HOME, "components")

    init_contents = f"""
from vulkan.dagster.workspace import make_workspace_definition
                 
definitions = make_workspace_definition("{code_entrypoint}", "{components_base_dir}")
"""
    with open(init_path, "w") as fp:
        fp.write(init_contents)

    return init_path

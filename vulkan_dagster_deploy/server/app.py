import base64
import json
import logging
import os
import subprocess
from shutil import rmtree
from typing import Annotated

from fastapi import Body, FastAPI, Form, HTTPException
from vulkan_dagster.dagster.workspace import add_workspace_config, unpack_workspace

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

DAGSTER_HOME = os.getenv("DAGSTER_HOME")
VENVS_PATH = os.getenv("VULKAN_VENVS_PATH")
SCRIPTS_PATH = os.getenv("VULKAN_SCRIPTS_PATH")


@app.post("/workspaces")
def create_workspace(
    name: Annotated[str, Body()],
    entrypoint: Annotated[str, Body()],
    repository: Annotated[str, Body()],
    dependencies: Annotated[list[str] | None, Body()] = None,
):
    repository = base64.b64decode(repository)
    logger.info(f"Creating workspace: {name} (python_module)")

    try:
        workspace_path = unpack_workspace(
            f"{DAGSTER_HOME}/workspaces", name, repository
        )

        completed_process = subprocess.run(
            ["bash", f"{SCRIPTS_PATH}/create_venv.sh", name, entrypoint],
            capture_output=True,
        )
        if completed_process.returncode != 0:
            msg = f"Failed to create virtual environment: {completed_process.stderr}"
            raise Exception(msg)

        add_workspace_config(DAGSTER_HOME, name, entrypoint)
        # TODO: check if the python modules names are unique
        # _install_components(name, workspace_path, path)
        if dependencies:
            _install_dependencies(name, dependencies)

        # TODO: These paths need to be configurable when creating the image.
        # Today we use hardcoded paths for scripts and venv.
        tmp_path = "/tmp/nodes.json"
        completed_process = subprocess.run(
            [
                f"{VENVS_PATH}/{name}/bin/python",
                f"{SCRIPTS_PATH}/extract_node_definitions.py",
                "--file_location",
                entrypoint,
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


def _install_dependencies(name, dependencies):
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

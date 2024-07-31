import base64
import logging
import os
import subprocess
from typing import Annotated

import yaml
from fastapi import FastAPI, Form, HTTPException

from vulkan_dagster.workspace import add_workspace_config, unpack_workspace

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

DAGSTER_HOME = os.getenv("DAGSTER_HOME")


@app.post("/workspaces/create")
def create_workspace(
    name: Annotated[str, Form()],
    path: Annotated[str, Form()],
    repository: Annotated[str, Form()],
):
    repository = base64.b64decode(repository)
    logger.info(f"Creating workspace: {name} (python_module)")

    try:
        workspace_path = unpack_workspace(
            f"{DAGSTER_HOME}/workspaces", name, repository
        )

        completed_process = subprocess.run(
            ["bash", "scripts/create_venv.sh", name, path],
            capture_output=True,
        )
        if completed_process.returncode != 0:
            msg = f"Failed to create virtual environment: {completed_process.stderr}"
            raise Exception(msg)

        add_workspace_config(DAGSTER_HOME, name, path)
        _install_components(name, workspace_path, path)

    except Exception as e:
        logger.error(f"Failed create workspace: {e}")
        raise HTTPException(status_code=500, detail=e)

    logger.info(f"Created workspace at: {workspace_path}")
    return {"status": "success", "path": workspace_path}


@app.post("/components/create")
def create_component(
    name: Annotated[str, Form()],
    repository: Annotated[bytes, Form()],
):
    repository = base64.b64decode(repository)
    logger.info(f"Creating component: {name}")

    try:
        base_dir = f"{DAGSTER_HOME}/components"
        component_path = unpack_workspace(base_dir, name, repository)
    except Exception as e:
        logger.error(f"Failed create component: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create component",
        )

    logger.info(f"Created component at: {component_path}")
    return {"status": "success"}


def _install_components(name, workspace_path, entrypoint):
    config_path = os.path.join(workspace_path, entrypoint, "vulkan.yaml")
    if not os.path.exists(config_path):
        raise ValueError(f"Config file not found at: {config_path}")

    with open(config_path, "r") as fn:
        config = yaml.safe_load(fn)
        # TODO: validate schema config
        # config = VulkanWorkspaceConfig.from_dict(config_data)

    if len(config["components"]) > 0:
        logger.info(f"Installing components for workspace: {name}")
        for component in config["components"]:
            result = subprocess.run(
                [
                    "bash",
                    "scripts/install_component.sh",
                    component["name"],
                    name,
                ],
                capture_output=True,
            )
            if result.returncode != 0:
                raise Exception(f"Failed to install component: {component['name']}")

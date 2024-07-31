from typing import Annotated
import base64
import os
import subprocess
import logging

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

        subprocess.run(
            ["bash", "scripts/create_venv.sh", name, path],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        add_workspace_config(DAGSTER_HOME, name, path)

        config_path = os.path.join(workspace_path, path, "vulkan.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as fn:
                config = yaml.safe_load(fn)

            if len(config["components"]) > 0:
                logger.info(f"Installing components for workspace: {name}")
                for component in config["components"]:
                    subprocess.run(
                        [
                            "bash",
                            "scripts/install_component.sh",
                            component["name"],
                            name,
                        ],
                        stderr=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                    )

    except Exception as e:
        logger.error(f"Failed create workspace: {e}")
        return HTTPException(
            status_code=500,
            detail="Failed to create workspace",
        )
        # return werkzeug.exceptions.InternalServerError(
        #     "Failed to create workspace",
        #     original_exception=e,
        # )

    logger.info(f"Created workspace at: {workspace_path}")
    return {"status": "success"}


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
        return HTTPException(
            status_code=500,
            detail="Failed to create component",
        )
        # return werkzeug.exceptions.InternalServerError(
        #     "Failed to create component",
        #     original_exception=e,
        # )

    logger.info(f"Created component at: {component_path}")
    return {"status": "success"}

import base64
import os
import subprocess

import werkzeug.exceptions
import yaml
from flask import Flask, Response, request

from vulkan_dagster.workspace import add_workspace_config, unpack_workspace

app = Flask("vulkan-dagster-server")

DAGSTER_HOME = os.getenv("DAGSTER_HOME")


@app.route("/workspaces/create", methods=["POST"])
def create_workspace():
    name = request.form["name"]
    path = request.form["path"]
    repository = request.form["repository"]
    repository = base64.b64decode(repository)
    app.logger.info(f"Creating workspace: {name} (python_module)")

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
        app.logger.error(f"Failed create workspace: {e}")
        return Response({"status": "error", "message": str(e)}, status=500)

    app.logger.info(f"Created workspace at: {workspace_path}")
    return {"status": "success", "path": workspace_path}


@app.route("/components/create", methods=["POST"])
def create_component():
    name = request.form["name"]
    repository = request.form["repository"]
    repository = base64.b64decode(repository)
    app.logger.info(f"Creating component: {name}")

    try:
        base_dir = f"{DAGSTER_HOME}/components"
        component_path = unpack_workspace(base_dir, name, repository)
    except Exception as e:
        app.logger.error(f"Failed create component: {e}")
        return werkzeug.exceptions.InternalServerError(
            "Failed to create component",
            original_exception=e,
        )

    app.logger.info(f"Created component at: {component_path}")
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
        app.logger.info(f"Installing components for workspace: {name}")
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

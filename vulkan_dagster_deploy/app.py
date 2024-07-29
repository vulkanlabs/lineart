import base64
import os
import subprocess

import werkzeug.exceptions
from flask import Flask, request

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
        base_dir = f"{DAGSTER_HOME}/workspaces"
        workspace_path = unpack_workspace(base_dir, name, repository)
        add_workspace_config(DAGSTER_HOME, name, path)
    except Exception as e:
        app.logger.error(f"Failed create workspace: {e}")
        return werkzeug.exceptions.InternalServerError(
            "Failed to create workspace",
            original_exception=e,
        )

    app.logger.info(f"Created workspace at: {workspace_path}")
    return {"status": "success"}


@app.route("/components/create", methods=["POST"])
def create_component():
    name = request.form["name"]
    repository = request.form["repository"]
    repository = base64.b64decode(repository)
    app.logger.info(f"Creating component: {name}")

    try:
        base_dir = f"{DAGSTER_HOME}/components"
        component_path = unpack_workspace(base_dir, name, repository)
        process = subprocess.run(
            ["poetry", "add", component_path],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        app.logger.debug(process.stdout)
        app.logger.debug(process.stderr)
    except Exception as e:
        app.logger.error(f"Failed create component: {e}")
        return werkzeug.exceptions.InternalServerError(
            "Failed to create component",
            original_exception=e,
        )

    app.logger.info(f"Created component at: {component_path}")
    return {"status": "success"}

import base64
import os

import werkzeug.exceptions
from flask import Flask, request

from vulkan_dagster.workspace import add_workspace_config, unpack_workspace

app = Flask("vulkan-dagster-server")

DAGSTER_HOME = os.getenv("DAGSTER_HOME")


@app.route("/workspace/create", methods=["POST"])
def create_workspace():
    name = request.form["name"]
    path = request.form["path"]
    repository = request.form["repository"]
    repository = base64.b64decode(repository)
    app.logger.info(f"Creating workspace: {name} (python_module)")

    try:
        workspace_path = unpack_workspace(DAGSTER_HOME, name, repository)
        add_workspace_config(DAGSTER_HOME, name, path)
    except Exception as e:
        app.logger.error(f"Failed create workspace: {e}")
        return werkzeug.exceptions.InternalServerError(
            "Failed to create workspace",
            original_exception=e,
        )

    app.logger.info(f"Created workspace at: {workspace_path}")
    return {"status": "success"}

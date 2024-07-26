import json
import os
import zipfile

import werkzeug.exceptions
from flask import Flask, request

app = Flask(__name__)

DAGSTER_HOME = os.getenv("DAGSTER_HOME")


@app.route("/workspace/create", methods=["POST"])
def create_workspace():
    name = request.form["name"]
    file = request.files["workspace"]
    app.logger.info(f"Creating workspace: {name} (python_module)")

    workspace_path = f"{DAGSTER_HOME}/workspaces/{name}/"
    with zipfile.ZipFile(file.stream._file) as zip_ref:
        zip_ref.extractall(workspace_path)
    _add_workspace_config(name)
    app.logger.info(f"Created workspace at: {workspace_path}")

    return {"status": "success"}


def _add_workspace_config(mode, name):
    with open(f"{DAGSTER_HOME}/workspace.yaml", "a") as ws:
        ws.write(
            (
                f"  - python_module:\n      module_name: {name}\n"
                "      working_directory: workspaces\n"
            )
        )

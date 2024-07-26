import os
import zipfile
from shutil import unpack_archive

from flask import Flask, request

app = Flask(__name__)

DAGSTER_HOME = os.getenv("DAGSTER_HOME")


@app.route("/workspace/create", methods=["POST"])
def create_workspace():
    name = request.form["name"]
    path = request.form["path"]
    file = request.files["workspace"]
    app.logger.info(f"Creating workspace: {name} (python_module)")

    workspace_path = f"{DAGSTER_HOME}/workspaces/{name}/"
    filepath = f".tmp.{name}"
    with open(filepath, "wb") as f:
        f.write(file.stream.read())
    unpack_archive(filepath, workspace_path, format="gztar")
    # with zipfile.ZipFile(file.stream._file) as zip_ref:
    #     zip_ref.extractall(workspace_path)
    _add_workspace_config(name, path)
    app.logger.info(f"Created workspace at: {workspace_path}")

    return {"status": "success"}


def _add_workspace_config(name: str, path: str):
    with open(f"{DAGSTER_HOME}/workspace.yaml", "a") as ws:
        ws.write(
            (
                "  - python_module:\n"
                f"      module_name: {path}\n"
                f"      working_directory: workspaces/{name}\n"
            )
        )

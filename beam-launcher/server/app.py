import json
import logging
import os
import subprocess

from fastapi import FastAPI

from server import routers, schemas
from server.workspace import VulkanWorkspaceManager

app = FastAPI()
app.include_router(routers.resources.router)

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


VENVS_PATH = os.getenv("VULKAN_VENVS_PATH")
SCRIPTS_PATH = os.getenv("VULKAN_SCRIPTS_PATH")


# TODO: make this endpoint ASYNC
@app.post("/backtest/launch")
def launch_backtest(config: schemas.BacktestConfig):
    logger.info(
        f"[{config.backtest_id}] Launching run for policy version: {config.policy_version_id}"
    )
    # prepare user code

    # 1. resolve policy and launch pipeline
    args = [
        f"{VENVS_PATH}/{config.policy_version_id}/bin/python",
        f"{SCRIPTS_PATH}/launch_dataflow.py",
    ]
    for key, value in config.model_dump().items():
        args.extend(["--" + key, json.dumps(value)])
    
    vm = VulkanWorkspaceManager(config.project_id, config.policy_version_id)
    args.extend(["--workspace_path", vm.workspace_path])
    args.extend(["--workspace_name", vm.workspace_name])
    args.extend(["--module_name", vm.code_location.module_name])
    args.extend(["--components_path", vm.components_path])

    logger.info(
        f"[{config.backtest_id}] Launching run for policy version: {config.policy_version_id}"
    )
    completed_process = subprocess.run(args, capture_output=True)

    if completed_process.returncode != 0:
        msg = f"Failed to launch dataflow pipeline: {completed_process.stderr}"
        raise Exception(msg)

    # 2. pool for status
    # when finished: results written directly to storage
    # 3. callback server to notify completion, passing: BacktestStatus, results_path
    pass

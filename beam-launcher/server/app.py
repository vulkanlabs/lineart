import logging
import os
from typing import Annotated

from apache_beam.options.pipeline_options import (
    GoogleCloudOptions,
    PipelineOptions,
    StandardOptions,
)
from fastapi import Body, FastAPI
from vulkan.beam.pipeline import BeamPipelineBuilder, DataEntryConfig
from vulkan.environment.loaders import resolve_policy

from server import routers
from server.workspace import VulkanWorkspaceManager

app = FastAPI()
app.include_router(routers.resources.router)

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_DATAFLOW_TEMP_LOCATION = os.getenv("GCP_DATAFLOW_TEMP_LOCATION")


@app.post("/backtest/launch")
def launch_backtest(
    project_id: Annotated[str, Body()],
    policy_version_id: Annotated[str, Body()],
    backtest_id: Annotated[str, Body()],
    data_sources: Annotated[dict[str, str], Body()],
    config_variables: Annotated[dict[str, str], Body()],
):
    logger.info(
        f"[{backtest_id}] Launching run for policy version: {policy_version_id}"
    )
    # prepare user code

    # 0. load policy
    vm = VulkanWorkspaceManager(project_id, policy_version_id)
    policy = resolve_policy(vm.code_location.entrypoint, vm.components_path)
    # 1. build pipeline
    data_sources = {
        name: DataEntryConfig(source=source) for name, source in data_sources.items()
    }

    options = PipelineOptions()
    options.view_as(StandardOptions).runner = "DataflowRunner"
    google_cloud_options = options.view_as(GoogleCloudOptions)
    google_cloud_options.project = GCP_PROJECT
    google_cloud_options.temp_location = GCP_DATAFLOW_TEMP_LOCATION

    pipeline = BeamPipelineBuilder(
        policy=policy,
        data_sources=data_sources,
        config_variables=config_variables,
        pipeline_options=options,
    ).build()
    # 2. launch pipeline
    pipeline.run()
    # 3. pool for status
    # when finished: results written directly to storage
    # 4. callback server to notify completion, passing: BacktestStatus, results_path
    pass

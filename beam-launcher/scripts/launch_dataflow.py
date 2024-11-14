import json
import logging
import os
from argparse import ArgumentParser
from dataclasses import dataclass

from apache_beam.options.pipeline_options import (
    GoogleCloudOptions,
    PipelineOptions,
    StandardOptions,
)
from vulkan.beam.pipeline import BeamPipelineBuilder, DataEntryConfig
from vulkan.core.policy import Policy
from vulkan.environment.loaders import resolve_policy

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION")
GCP_DATAFLOW_WORKER_SA = os.getenv("GCP_DATAFLOW_WORKER_SA")
GCP_DATAFLOW_TEMP_LOCATION = os.getenv("GCP_DATAFLOW_TEMP_LOCATION")
GCP_DATAFLOW_STAGING_LOCATION = os.getenv("GCP_DATAFLOW_STAGING_LOCATION")
GCP_DATAFLOW_OUTPUT_BUCKET = os.getenv("GCP_DATAFLOW_OUTPUT_BUCKET")

VULKAN_LIB_PATH = os.getenv("VULKAN_LIB_PATH")
VULKAN_SERVER_PATH = os.getenv("VULKAN_SERVER_PATH")


@dataclass
class BacktestConfig:
    project_id: str
    policy_version_id: str
    backtest_id: str
    data_sources: dict[str, str]
    config_variables: dict[str, str] | None = None


def launch_pipeline(
    project_id: str,
    backtest_id: str,
    image: str,
    data_sources: dict[str, str],
    policy: Policy,
    config_variables: dict[str, str] | None = None,
):
    data_sources = {
        name: DataEntryConfig(source=source) for name, source in data_sources.items()
    }
    worker_options = ["--machine_type=n1-standard-4"]
    sdk = [
        "--experiments=use_runner_v2",
        f"--sdk_container_image={image}",
        "--sdk_location=container",
    ]
    flags = sdk + worker_options

    pipeline_options = PipelineOptions(flags)
    pipeline_options.view_as(StandardOptions).runner = "DataflowRunner"
    google_cloud_options = pipeline_options.view_as(GoogleCloudOptions)
    google_cloud_options.project = GCP_PROJECT_ID
    google_cloud_options.region = GCP_REGION
    google_cloud_options.temp_location = f"gs://{GCP_DATAFLOW_TEMP_LOCATION}"
    google_cloud_options.staging_location = f"gs://{GCP_DATAFLOW_STAGING_LOCATION}"
    google_cloud_options.service_account_email = (
        f"{GCP_DATAFLOW_WORKER_SA}@{GCP_PROJECT_ID}.iam.gserviceaccount.com"
    )

    pipeline = BeamPipelineBuilder(
        policy=policy,
        project_id=project_id,
        backtest_id=backtest_id,
        output_bucket=GCP_DATAFLOW_OUTPUT_BUCKET,
        data_sources=data_sources,
        config_variables=config_variables,
        pipeline_options=pipeline_options,
    ).build()

    pipeline.run()


if __name__ == "__main__":
    parser = ArgumentParser()
    # Backtest config args
    parser.add_argument("--project_id", type=str)
    parser.add_argument("--backtest_id", type=str)
    parser.add_argument("--image", type=str)
    parser.add_argument("--data_sources", type=str)
    parser.add_argument("--config_variables", type=str)
    # Code location args
    parser.add_argument("--workspace_path", type=str)
    parser.add_argument("--workspace_name", type=str)
    parser.add_argument("--module_name", type=str)
    parser.add_argument("--components_path", type=str)
    args = parser.parse_args()

    data_sources = json.loads(args.data_sources)

    if args.config_variables:
        config_variables = json.loads(args.config_variables)
    else:
        config_variables = None

    policy = resolve_policy(args.module_name, args.components_path)
    launch_pipeline(
        project_id=args.project_id,
        backtest_id=args.backtest_id,
        data_sources=data_sources,
        config_variables=config_variables,
        policy=policy,
        image=args.image,
    )

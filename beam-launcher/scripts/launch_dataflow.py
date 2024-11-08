import json
import logging
import os
import subprocess
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
from vulkan_public.spec.environment.loaders import load_policy_definition

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION")
GCP_DATAFLOW_WORKER_SA = os.getenv("GCP_DATAFLOW_WORKER_SA")
GCP_DATAFLOW_TEMP_LOCATION = os.getenv("GCP_DATAFLOW_TEMP_LOCATION")
GCP_DATAFLOW_STAGING_LOCATION = os.getenv("GCP_DATAFLOW_STAGING_LOCATION")

VULKAN_LIB_PATH = os.getenv("VULKAN_LIB_PATH")
VULKAN_SERVER_PATH = os.getenv("VULKAN_SERVER_PATH")
VULKAN_STAGING_PATH = os.getenv("VULKAN_STAGING_PATH")


@dataclass
class BacktestConfig:
    project_id: str
    policy_version_id: str
    backtest_id: str
    data_sources: dict[str, str]
    config_variables: dict[str, str] | None = None


def launch_pipeline(
    project_id: str,
    policy_version_id: str,
    backtest_id: str,
    data_sources: dict[str, str],
    policy: Policy,
    packages: list[str],
    config_variables: dict[str, str] | None = None,
):
    data_sources = {
        name: DataEntryConfig(source=source) for name, source in data_sources.items()
    }
    extra_packages = [f"--extra_package={package}" for package in packages]
    worker_options = ["--machine_type=n1-standard-4"]
    flags = extra_packages + worker_options

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
        data_sources=data_sources,
        config_variables=config_variables,
        pipeline_options=pipeline_options,
    ).build()
    # 2. launch pipeline
    pipeline.run()


def create_packages(workspace_path, workspace_name, module_name, components_path):
    policy_definition = load_policy_definition(module_name)
    staging_dir = os.path.join(VULKAN_STAGING_PATH, workspace_name)
    packages = [workspace_path]

    for component_instance in policy_definition.components:
        alias = component_instance.alias()
        packages.append(os.path.join(components_path, alias))

    for package in packages:
        process = subprocess.run(
            ["python", "-m", "build", package, "--outdir", staging_dir, "--sdist"],
            capture_output=True,
        )
        if process.returncode != 0:
            raise Exception(f"Failed to create package: {package}", process.stderr)

    packages = [fn for fn in os.listdir(staging_dir) if fn.endswith(".tar.gz")]
    return [os.path.join(staging_dir, fn) for fn in packages]


if __name__ == "__main__":
    parser = ArgumentParser()
    # Backtest config args
    parser.add_argument("--project_id", type=str)
    parser.add_argument("--policy_version_id", type=str)
    parser.add_argument("--backtest_id", type=str)
    parser.add_argument("--data_sources", type=str)
    parser.add_argument("--config_variables", type=str)
    # Code location args
    parser.add_argument("--workspace_path", type=str)
    parser.add_argument("--workspace_name", type=str)
    parser.add_argument("--module_name", type=str)
    parser.add_argument("--components_path", type=str)
    args = parser.parse_args()

    data_sources = json.loads(args.data_sources)
    config_variables = json.loads(args.config_variables)

    policy = resolve_policy(args.module_name, args.components_path)

    user_packages = create_packages(
        workspace_path=args.workspace_path,
        workspace_name=args.workspace_name,
        module_name=args.module_name,
        components_path=args.components_path,
    )
    libs = [fn for fn in os.listdir(VULKAN_LIB_PATH) if fn.endswith(".tar.gz")]
    vulkan_packages = [os.path.join(VULKAN_LIB_PATH, fn) for fn in libs]
    packages = user_packages + vulkan_packages

    launch_pipeline(
        project_id=args.project_id,
        policy_version_id=args.policy_version_id,
        backtest_id=args.backtest_id,
        data_sources=data_sources,
        config_variables=config_variables,
        policy=policy,
        packages=packages,
    )

    # Remove staging resources for this workspace
    subprocess.run(
        ["rm", "-rf", os.path.join(VULKAN_STAGING_PATH, args.workspace_name)]
    )

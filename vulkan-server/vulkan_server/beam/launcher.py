import json
import os
from datetime import datetime
from typing import Any

from google.cloud import dataflow_v1beta3 as dataflow
from pydantic.dataclasses import dataclass

from vulkan_server.logger import init_logger

logger = init_logger("beam-launcher")


@dataclass
class DataflowConfig:
    service_account: str
    machine_type: str
    temp_location: str
    staging_location: str
    output_bucket: str
    templates_path: str
    project: str
    region: str = "us-central1"


def get_dataflow_config() -> DataflowConfig:
    return DataflowConfig(
        project=os.getenv("GCP_DATAFLOW_PROJECT_ID", None),
        region=os.getenv("GCP_DATAFLOW_REGION", None),
        service_account=os.getenv("GCP_DATAFLOW_SERVICE_ACCOUNT_EMAIL", None),
        machine_type=os.getenv("GCP_DATAFLOW_MACHINE_TYPE", None),
        temp_location=os.getenv("GCP_DATAFLOW_TEMP_LOCATION", None),
        staging_location=os.getenv("GCP_DATAFLOW_STAGING_LOCATION", None),
        output_bucket=os.getenv("GCP_DATAFLOW_OUTPUT_BUCKET", None),
        templates_path=os.getenv("GCP_DATAFLOW_TEMPLATES_PATH", None),
    )


def get_dataflow_client() -> dataflow.FlexTemplatesServiceClient:
    return dataflow.FlexTemplatesServiceClient()


def launch_run(
    policy_version_id: str,
    project_id: str,
    backtest_id: str,
    image: str,
    module_name: str,
    data_sources: dict,
    components_path: str,
    config_variables: dict[str, Any] | None = None,
):
    dataflow_client = get_dataflow_client()
    config = get_dataflow_config()

    environment = dataflow.FlexTemplateRuntimeEnvironment(
        num_workers=1,
        max_workers=5,
        sdk_container_image=image,
        temp_location=config.temp_location,
        staging_location=config.staging_location,
        machine_type=config.machine_type,
        service_account_email=config.service_account,
    )

    launch_time = datetime.now()
    job_name = f"test-run-{policy_version_id}-{launch_time.strftime('%Y%m%d-%H%M%S')}"

    script_params = {
        "output_path": f"{config.output_bucket}/{project_id}/{backtest_id}",
        "data_sources": json.dumps(data_sources),
        "module_name": module_name,
        "components_path": components_path,
        "image": image,
    }

    template_file_gcs_location = os.path.join(
        config.templates_path, f"{policy_version_id}.json"
    )

    job_parameters = dataflow.LaunchFlexTemplateParameter(
        job_name=job_name,
        container_spec_gcs_path=template_file_gcs_location,
        environment=environment,
        parameters=script_params,
    )

    job_request = dataflow.LaunchFlexTemplateRequest(
        project_id=config.project,
        location=config.region,
        launch_parameter=job_parameters,
    )

    response = dataflow_client.launch_flex_template(request=job_request)
    return {
        "job_id": response.job.id,
        "project_id": response.job.project_id,
        "name": response.job.name,
        "create_time": response.job.create_time,
        "current_state": response.job.current_state,
    }

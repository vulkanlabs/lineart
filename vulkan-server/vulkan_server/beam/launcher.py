import os
from datetime import datetime

from fastapi import Depends
from google.cloud import dataflow_v1beta3 as dataflow
from pydantic.dataclasses import dataclass


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
    GCP_DATAFLOW_SERVICE_ACCOUNT_EMAIL = os.getenv("GCP_DATAFLOW_SERVICE_ACCOUNT_EMAIL")
    GCP_DATAFLOW_MACHINE_TYPE = os.getenv("GCP_DATAFLOW_MACHINE_TYPE")
    GCP_DATAFLOW_TEMP_LOCATION = os.getenv("GCP_DATAFLOW_TEMP_LOCATION")
    GCP_DATAFLOW_STAGING_LOCATION = os.getenv("GCP_DATAFLOW_STAGING_LOCATION")
    GCP_DATAFLOW_PROJECT = os.getenv("GCP_DATAFLOW_PROJECT")
    GCP_DATAFLOW_REGION = os.getenv("GCP_DATAFLOW_REGION")
    GCP_DATAFLOW_OUTPUT_BUCKET = os.getenv("GCP_DATAFLOW_OUTPUT_BUCKET")
    GCP_DATAFLOW_TEMPLATES_PATH = os.getenv("GCP_DATAFLOW_TEMPLATES_PATH")

    if (
        GCP_DATAFLOW_SERVICE_ACCOUNT_EMAIL is None
        or GCP_DATAFLOW_MACHINE_TYPE is None
        or GCP_DATAFLOW_TEMP_LOCATION is None
        or GCP_DATAFLOW_STAGING_LOCATION is None
        or GCP_DATAFLOW_PROJECT is None
        or GCP_DATAFLOW_REGION is None
        or GCP_DATAFLOW_OUTPUT_BUCKET is None
        or GCP_DATAFLOW_TEMPLATES_PATH is None
    ):
        raise ValueError("Dataflow configuration is missing")

    return DataflowConfig(
        project=GCP_DATAFLOW_PROJECT,
        region=GCP_DATAFLOW_REGION,
        service_account=GCP_DATAFLOW_SERVICE_ACCOUNT_EMAIL,
        machine_type=GCP_DATAFLOW_MACHINE_TYPE,
        temp_location=GCP_DATAFLOW_TEMP_LOCATION,
        staging_location=GCP_DATAFLOW_STAGING_LOCATION,
        output_bucket=GCP_DATAFLOW_OUTPUT_BUCKET,
        templates_path=GCP_DATAFLOW_TEMPLATES_PATH,
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
    dataflow_client=Depends(get_dataflow_client),
    config=Depends(get_dataflow_config),
):
    environment = (
        dataflow.FlexTemplateRuntimeEnvironment(
            num_workers=1,
            max_workers=5,
            sdk_container_image=image,
            temp_location=config.temp_location,
            staging_location=config.staging_location,
            machine_type=config.machine_type,
            service_account_email=config.service_account,
        ),
    )

    launch_time = datetime.now()
    job_name = f"test-run-{policy_version_id}-{launch_time.strftime('%Y%m%d-%H%M%S')}"

    script_params = {
        "output_path": f"{config.output_bucket}/{project_id}/{backtest_id}",
        "data_sources": data_sources,
        "module_name": module_name,
        "components_path": components_path,
        "image": image,
    }

    template_file_gcs_location = f"{config.templates_path}/{policy_version_id}.json"

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

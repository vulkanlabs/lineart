import json
import os
from datetime import datetime
from typing import Any

from google.cloud import dataflow_v1beta3 as dataflow
from pydantic.dataclasses import dataclass

from vulkan_server.logger import init_logger

logger = init_logger("beam-launcher")


class DataflowLauncher:
    def __init__(self, components_path: str) -> None:
        self.components_path = components_path

        self.config: DataflowConfig = _get_dataflow_config()
        self.dataflow_client = dataflow.FlexTemplatesServiceClient()

    def launch_run(
        self,
        policy_version_id: str,
        project_id: str,
        backtest_id: str,
        image: str,
        module_name: str,
        data_sources: dict,
        config_variables: dict[str, Any] | None = None,
    ):
        environment = dataflow.FlexTemplateRuntimeEnvironment(
            num_workers=1,
            max_workers=5,
            sdk_container_image=image,
            temp_location=self.config.temp_location,
            staging_location=self.config.staging_location,
            machine_type=self.config.machine_type,
            service_account_email=self.config.service_account,
        )

        launch_time = datetime.now()
        job_name = (
            f"policy-{policy_version_id}-t-{launch_time.strftime('%Y%m%d-%H%M%S')}"
        )

        if config_variables is None:
            config_variables = {}

        script_params = {
            "output_path": f"{self.config.output_bucket}/{project_id}/{backtest_id}",
            "data_sources": json.dumps(data_sources),
            "module_name": module_name,
            "components_path": self.components_path,
            "image": image,
            "config_variables": json.dumps(config_variables),
        }

        template_file_gcs_location = os.path.join(
            self.config.templates_path, f"{policy_version_id}.json"
        )

        job_parameters = dataflow.LaunchFlexTemplateParameter(
            job_name=job_name,
            container_spec_gcs_path=template_file_gcs_location,
            environment=environment,
            parameters=script_params,
        )

        job_request = dataflow.LaunchFlexTemplateRequest(
            project_id=self.config.project,
            location=self.config.region,
            launch_parameter=job_parameters,
        )

        response = self.dataflow_client.launch_flex_template(request=job_request)
        # TODO: check if launch succeeded
        logger.info(f"Launched backtest {backtest_id} with job id {response.job.id}")
        return LaunchRunResponse(
            job_id=response.job.id,
            project_id=response.job.project_id,
        )


def get_launcher() -> DataflowLauncher:
    # TODO: get components path from config
    return DataflowLauncher(components_path="/opt/dependencies/")


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


def _get_dataflow_config() -> DataflowConfig:
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


@dataclass
class LaunchRunResponse:
    job_id: str
    project_id: str

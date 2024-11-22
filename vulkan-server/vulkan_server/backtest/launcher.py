import json
import os
from datetime import datetime
from typing import Any

from fastapi import Depends
from google.cloud import dataflow_v1beta3 as dataflow
from pydantic.dataclasses import dataclass
from sqlalchemy.orm import Session
from vulkan.core.run import RunStatus
from vulkan_public.spec.dependency import INPUT_NODE

from vulkan_server import schemas
from vulkan_server.db import Backfill, BeamWorkspace, PolicyVersion, get_db
from vulkan_server.logger import init_logger

logger = init_logger("beam-launcher")


class BackfillLauncher:
    def __init__(self, db: Session) -> None:
        self.db: Session = db
        # FIXME: This path should be set by a shared environment variable
        self.backend_launcher = _DataflowLauncher(components_path="/opt/dependencies/")

    def create_backfill(
        self,
        project_id: str,
        backtest_id: str,
        policy_version: PolicyVersion,
        workspace: BeamWorkspace,
        input_data_path: str,
        resolved_config_variables: dict | None,
    ) -> schemas.Backfill:
        # TODO: Maybe we don't need to pass the entire policy version obj here
        backfill = Backfill(
            backtest_id=backtest_id,
            input_data_path=input_data_path,
            status=RunStatus.PENDING,
            config_variables=resolved_config_variables,
            project_id=project_id,
        )
        self.db.add(backfill)
        self.db.commit()

        output_path = f"{self.backend_launcher.config.output_bucket}/{project_id}/{backfill.backfill_id}"
        backfill.output_path = output_path

        response = self.backend_launcher.launch_run(
            policy_version_id=str(policy_version.policy_version_id),
            backfill_id=str(backfill.backfill_id),
            image=workspace.image,
            module_name=policy_version.module_name,
            data_sources={
                INPUT_NODE: backfill.input_data_path,
            },
            config_variables=resolved_config_variables,
            output_path=output_path,
        )
        backfill.gcp_project_id = response.project_id
        backfill.gcp_job_id = response.job_id
        self.db.commit()

        logger.info(f"Launched run {response}")

        return backfill


def get_launcher(db: Session = Depends(get_db)) -> BackfillLauncher:
    return BackfillLauncher(db=db)


class _DataflowLauncher:
    def __init__(self, components_path: str) -> None:
        self.components_path = components_path

        self.config: DataflowConfig = _get_dataflow_config()
        self.dataflow_client = dataflow.FlexTemplatesServiceClient()

    def launch_run(
        self,
        policy_version_id: str,
        backfill_id: str,
        image: str,
        module_name: str,
        data_sources: dict,
        config_variables: dict[str, Any] | None,
        output_path: str,
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
        job_name = f"job-{backfill_id}-t-{launch_time.strftime('%Y%m%d-%H%M%S')}"

        if config_variables is None:
            config_variables = {}

        script_params = {
            "backfill_id": backfill_id,
            "output_path": output_path,
            "data_sources": json.dumps(data_sources),
            "module_name": module_name,
            "components_path": self.components_path,
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
        logger.info(f"Launched backfill {backfill_id} with job id {response.job.id}")
        return _LaunchRunResponse(
            job_id=response.job.id,
            project_id=response.job.project_id,
        )


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
class _LaunchRunResponse:
    job_id: str
    project_id: str


def get_dataflow_job_state(job_id: str) -> dataflow.JobState:
    config = _get_dataflow_config()
    client = dataflow.JobsV1Beta3Client()
    request = dataflow.GetJobRequest(
        project_id=config.project,
        location=config.region,
        job_id=job_id,
        view=dataflow.JobView.JOB_VIEW_SUMMARY,
    )
    job = client.get_job(request=request)
    return job.current_state


def get_backfill_job_status(gcp_job_id: str) -> str:
    dataflow_job_state = get_dataflow_job_state(gcp_job_id)
    return _JOB_STATE_MAP.get(dataflow_job_state, "UNKNOWN")


_JOB_STATE_MAP = {
    # Creating / Running states
    dataflow.JobState.JOB_STATE_UNKNOWN: RunStatus.PENDING.name,
    dataflow.JobState.JOB_STATE_QUEUED: RunStatus.PENDING.name,
    dataflow.JobState.JOB_STATE_PENDING: RunStatus.PENDING.name,
    dataflow.JobState.JOB_STATE_STOPPED: RunStatus.PENDING.name,
    dataflow.JobState.JOB_STATE_RUNNING: RunStatus.STARTED.name,
    # Terminal states
    dataflow.JobState.JOB_STATE_FAILED: RunStatus.FAILURE.name,
    dataflow.JobState.JOB_STATE_DONE: RunStatus.SUCCESS.name,
    # States unlikely to be reached. They require explicit actions
    # not covered by the current implementation.
    dataflow.JobState.JOB_STATE_UPDATED: RunStatus.PENDING.name,
    dataflow.JobState.JOB_STATE_CANCELLING: RunStatus.FAILURE.name,
    dataflow.JobState.JOB_STATE_CANCELLED: RunStatus.FAILURE.name,
    dataflow.JobState.JOB_STATE_DRAINING: RunStatus.FAILURE.name,
    dataflow.JobState.JOB_STATE_DRAINED: RunStatus.FAILURE.name,
    dataflow.JobState.JOB_STATE_RESOURCE_CLEANING_UP: RunStatus.SUCCESS.name,
}

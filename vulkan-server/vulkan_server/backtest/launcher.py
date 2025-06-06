import json
import os
from datetime import datetime
from typing import Any

from fastapi import Depends
from google.cloud import dataflow_v1beta3 as dataflow
from pydantic.dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session

from vulkan.core.run import RunStatus
from vulkan.schemas import DataSourceSpec
from vulkan_server import schemas
from vulkan_server.db import (
    Backfill,
    BacktestMetrics,
    BeamWorkspace,
    DataSource,
    PolicyDataDependency,
    PolicyVersion,
    get_db,
)
from vulkan_server.logger import init_logger

logger = init_logger("beam-launcher")


class BacktestLauncher:
    def __init__(self, db: Session) -> None:
        self.db: Session = db
        # FIXME: This path should be set by a shared environment variable
        self.backend_launcher = _DataflowLauncher(components_path="/opt/dependencies/")

    def backtest_output_path(self, backtest_id: str) -> str:
        return os.path.join(
            self.backend_launcher.config.output_bucket,
            self.backend_launcher.config.project,
            str(backtest_id),
        )

    def create_backfill(
        self,
        backtest_id: str,
        policy_version: PolicyVersion,
        workspace: BeamWorkspace,
        input_data_path: str,
        resolved_config_variables: dict | None,
    ) -> schemas.Backfill:
        backfill = Backfill(
            backtest_id=backtest_id,
            input_data_path=input_data_path,
            status=RunStatus.PENDING,
            config_variables=resolved_config_variables,
        )
        self.db.add(backfill)
        self.db.commit()

        data_sources = get_required_data_source_specs(policy_version, self.db)

        output_path = os.path.join(
            self.backtest_output_path(backtest_id),
            "backfills",
            str(backfill.backfill_id),
        )
        backfill.output_path = output_path
        response = self.backend_launcher.launch_run(
            policy_version_id=str(policy_version.policy_version_id),
            backfill_id=str(backfill.backfill_id),
            image=workspace.image,
            module_name=policy_version.module_name,
            input_data_path=backfill.input_data_path,
            data_sources=data_sources,
            config_variables=resolved_config_variables,
            output_path=output_path,
        )
        backfill.gcp_project_id = response.project_id
        backfill.gcp_job_id = response.job_id
        self.db.commit()

        logger.info(f"Launched run {response}")

        return backfill

    def create_metrics(
        self,
        backtest_id: str,
        input_data_path: str,
        results_data_path: str,
        target_column: str,
        time_column: str | None = None,
        group_by_columns: list[str] | None = None,
    ) -> schemas.Backfill:
        output_path = os.path.join(
            self.backtest_output_path(backtest_id),
            "metrics",
        )
        metrics = BacktestMetrics(
            backtest_id=backtest_id,
            status=RunStatus.PENDING,
            output_path=os.path.join(output_path, "metrics.json"),
        )
        self.db.add(metrics)
        self.db.commit()

        response = self.backend_launcher.launch_metrics_run(
            backtest_id=backtest_id,
            input_data_path=input_data_path,
            results_data_path=results_data_path,
            output_path=output_path,
            outcome_column="status",
            target_column=target_column,
            time_column=time_column,
            group_by_columns=group_by_columns,
        )

        metrics.gcp_project_id = response.project_id
        metrics.gcp_job_id = response.job_id
        self.db.commit()

        logger.info(f"Launched run {response}")
        return metrics


def get_launcher(db: Session = Depends(get_db)) -> BacktestLauncher:
    return BacktestLauncher(db=db)


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
        input_data_path: str,
        data_sources: list[DataSourceSpec],
        config_variables: dict[str, Any] | None,
        output_path: str,
    ):
        environment = self._environment_configuration(
            num_workers=1, max_workers=5, sdk_container_image=image
        )

        launch_time = datetime.now()
        job_name = f"job-{backfill_id}-t-{launch_time.strftime('%Y%m%d-%H%M%S')}"

        if config_variables is None:
            config_variables = {}

        data_sources = [s.model_dump_json() for s in data_sources]
        script_params = {
            "backfill_id": backfill_id,
            "input_data_path": input_data_path,
            "data_sources": json.dumps(data_sources),
            "output_path": output_path,
            "module_name": module_name,
            "components_path": self.components_path,
            "config_variables": json.dumps(config_variables),
        }

        template_file_gcs_location = os.path.join(
            self.config.templates_path, f"{policy_version_id}.json"
        )

        response = self._launch_flex_template_run(
            job_name=job_name,
            template_file_gcs_location=template_file_gcs_location,
            environment=environment,
            script_params=script_params,
        )

        logger.info(f"Launched backfill {backfill_id} with job id {response.job_id}")
        return response

    def launch_metrics_run(
        self,
        backtest_id: str,
        input_data_path: str,
        results_data_path: str,
        output_path: str,
        outcome_column: str,
        target_column: str,
        time_column: str | None,
        group_by_columns: list[str] | None,
    ):
        script_params = {
            "backtest_id": backtest_id,
            "input_data_path": input_data_path,
            "results_data_path": results_data_path,
            "output_path": output_path,
            "outcome": outcome_column,
            "target_name": target_column,
            "target_kind": "BINARY_DISTRIBUTION",
        }
        if time_column is not None:
            script_params["time"] = time_column
        if group_by_columns is not None:
            script_params["groups"] = json.dumps(group_by_columns)

        logger.debug(f"Launching metrics for {backtest_id}")
        logger.debug(f"Script params: {script_params}")

        template_file_gcs_location = os.path.join(
            self.config.templates_path, "metrics-pipeline.json"
        )

        image = f"{self.config.region}-docker.pkg.dev/{self.config.project}/docker-images/metrics-pipeline:latest"
        environment = self._environment_configuration(
            num_workers=1,
            max_workers=5,
            sdk_container_image=image,
        )

        job_name = f"metrics-{backtest_id}"
        response = self._launch_flex_template_run(
            job_name=job_name,
            template_file_gcs_location=template_file_gcs_location,
            environment=environment,
            script_params=script_params,
        )

        logger.info(f"Launched metrics for {backtest_id} with job id {response.job_id}")
        return response

    def _launch_flex_template_run(
        self,
        job_name: str,
        template_file_gcs_location: str,
        environment: dataflow.FlexTemplateRuntimeEnvironment,
        script_params: dict[str, str],
    ):
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

        response: dataflow.LaunchFlexTemplateResponse = (
            self.dataflow_client.launch_flex_template(request=job_request)
        )

        # TODO: check if launch succeeded
        return _LaunchRunResponse(
            job_id=response.job.id,
            project_id=response.job.project_id,
        )

    def _environment_configuration(
        self, num_workers, max_workers: int, sdk_container_image: str
    ):
        return dataflow.FlexTemplateRuntimeEnvironment(
            num_workers=num_workers,
            max_workers=max_workers,
            sdk_container_image=sdk_container_image,
            temp_location=self.config.temp_location,
            staging_location=self.config.staging_location,
            machine_type=self.config.machine_type,
            service_account_email=self.config.service_account,
            network=self.config.network,
            subnetwork=self.config.subnetwork,
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
    region: str
    network: str
    subnetwork: str


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
        network=os.getenv("GCP_DATAFLOW_NETWORK", None),
        subnetwork=os.getenv("GCP_DATAFLOW_SUBNETWORK", None),
    )


@dataclass
class _LaunchRunResponse:
    job_id: str
    project_id: str


def _get_dataflow_job_state(job_id: str) -> dataflow.JobState:
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


def get_backtest_job_status(gcp_job_id: str) -> RunStatus:
    dataflow_job_state = _get_dataflow_job_state(gcp_job_id)
    return _JOB_STATE_MAP.get(dataflow_job_state, RunStatus.PENDING)


async def _async_get_dataflow_job_state(job_id: str) -> dataflow.JobState:
    config = _get_dataflow_config()
    client = dataflow.JobsV1Beta3AsyncClient()
    request = dataflow.GetJobRequest(
        project_id=config.project,
        location=config.region,
        job_id=job_id,
        view=dataflow.JobView.JOB_VIEW_SUMMARY,
    )
    job = await client.get_job(request=request)
    return job.current_state


async def async_get_backtest_job_status(gcp_job_id: str) -> RunStatus:
    dataflow_job_state = await _async_get_dataflow_job_state(gcp_job_id)
    return _JOB_STATE_MAP.get(dataflow_job_state, RunStatus.PENDING)


_JOB_STATE_MAP = {
    # Creating / Running states
    dataflow.JobState.JOB_STATE_UNKNOWN: RunStatus.PENDING,
    dataflow.JobState.JOB_STATE_QUEUED: RunStatus.PENDING,
    dataflow.JobState.JOB_STATE_PENDING: RunStatus.PENDING,
    dataflow.JobState.JOB_STATE_STOPPED: RunStatus.PENDING,
    dataflow.JobState.JOB_STATE_RUNNING: RunStatus.STARTED,
    # Terminal states
    dataflow.JobState.JOB_STATE_FAILED: RunStatus.FAILURE,
    dataflow.JobState.JOB_STATE_DONE: RunStatus.SUCCESS,
    # States unlikely to be reached. They require explicit actions
    # not covered by the current implementation.
    dataflow.JobState.JOB_STATE_UPDATED: RunStatus.PENDING,
    dataflow.JobState.JOB_STATE_CANCELLING: RunStatus.FAILURE,
    dataflow.JobState.JOB_STATE_CANCELLED: RunStatus.FAILURE,
    dataflow.JobState.JOB_STATE_DRAINING: RunStatus.FAILURE,
    dataflow.JobState.JOB_STATE_DRAINED: RunStatus.FAILURE,
    dataflow.JobState.JOB_STATE_RESOURCE_CLEANING_UP: RunStatus.SUCCESS,
}


def get_required_data_source_specs(
    policy_version: PolicyVersion,
    db: Session,
) -> list[DataSourceSpec]:
    q = select(DataSource).where(
        DataSource.data_source_id.in_(
            select(PolicyDataDependency.data_source_id).where(
                PolicyDataDependency.policy_version_id
                == policy_version.policy_version_id
            )
        )
    )
    data_sources = db.execute(q).scalars().all()

    return [s.to_spec() for s in data_sources]

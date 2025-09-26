import logging

from hatchet_sdk import ClientConfig, Hatchet
from hatchet_sdk.clients.rest.exceptions import ApiException
from hatchet_sdk.clients.rest.models import V1TaskStatus, V1TaskSummary

from vulkan_engine.backends.data_client import BaseDataClient
from vulkan_engine.config import WorkerServiceConfig
from vulkan_engine.schemas import LogEntry, StepDetails, StepMetadataBase


class HatchetDataClient(BaseDataClient):
    def __init__(
        self,
        worker_config: WorkerServiceConfig,
        logger: logging.Logger | None = None,
    ):
        client_cfg = ClientConfig(
            token=worker_config.service_config.hatchet_token,
            # TODO: allow configuring the server URL
        )
        self.hatchet_client = Hatchet(config=client_cfg)
        self.logger = logger or logging.getLogger(__name__)

    def get_run_data(self, run_id: str) -> dict[str, StepDetails]:
        try:
            hatchet_run = self.hatchet_client.runs.get(run_id)
        except ApiException as e:
            self.logger.error(f"Exception when calling Hatchet API: {e}")
            raise ValueError(f"Failed to fetch run data for run_id {run_id}") from e

        if len(hatchet_run.tasks) == 0:
            self.logger.debug(f"No tasks found for run_id {run_id}")
            return {}

        details: dict[str, StepDetails] = {}
        for t in hatchet_run.tasks:
            step_details = _metadata_from_hatchet_v1_task(t)
            if step_details is not None:
                details[step_details.metadata.step_name] = step_details
        return details

    def get_run_logs(self, run_id: str) -> list[LogEntry]:
        try:
            run = self.hatchet_client.runs.get(run_id)
        except ApiException as e:
            self.logger.error(f"Exception when calling Hatchet API: {e}")
            raise ValueError(f"Failed to fetch run logs for run_id {run_id}") from e

        logs = []
        for task in run.tasks:
            try:
                task_logs = self.hatchet_client.logs.list(task.metadata.id)
                # TODO: this implementation doesn't deal with pagination yet.
                # We should handle this here by iterating through all pages.

                for row in task_logs.rows:
                    entry = LogEntry(
                        timestamp=row.created_at,
                        step_key=_step_name_from_action_id(task),
                        source="USER",
                        event={
                            "log_type": "LOG",
                            "message": row.message,
                            "level": row.level.value,
                        },
                    )
                    logs.append(entry)
            except ApiException as e:
                self.logger.error(
                    f"Exception when fetching logs for task {task.id}: {e}"
                )
                continue  # Skip this task's logs on error
        return logs


def _metadata_from_hatchet_v1_task(t: V1TaskSummary) -> StepDetails | None:
    if t.started_at is None:
        return None

    output = None
    node_type = ""
    if t.status == V1TaskStatus.COMPLETED:
        output = t.output["data"]
        node_type = t.output["step_type"]

    step_name = _step_name_from_action_id(t)
    metadata = StepMetadataBase(
        step_name=step_name,
        node_type=node_type,
        start_time=t.started_at.timestamp(),
        end_time=t.finished_at.timestamp(),
        error=t.error_message,
    )

    return StepDetails(
        output=output,
        metadata=metadata,
    )


def _step_name_from_action_id(task: V1TaskSummary) -> str:
    # Hatchet action IDs are in the format "<workflow_uuid>:<step_name>"
    _, _, step_name = task.action_id.rpartition(":")
    return step_name

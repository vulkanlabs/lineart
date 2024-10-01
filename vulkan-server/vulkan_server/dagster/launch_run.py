from uuid import UUID

from sqlalchemy.orm import Session
from vulkan.core.run import RunStatus
import json
from vulkan.dagster.policy import DEFAULT_POLICY_NAME

from vulkan_server.dagster import trigger_run
from vulkan_server.db import Run


def launch_run(
    dagster_client,
    server_url: str,
    execution_config: dict,
    policy_version_id: UUID,
    version_name: str,
    db: Session,
    project_id: str,
):
    run = Run(policy_version_id=policy_version_id, status=RunStatus.PENDING, project_id=project_id)
    db.add(run)
    db.commit()

    error_msg = ""
    # TODO: We should separate dagster and core db functionality to ensure its
    # easy to migrate to other execution engines.
    try:
        dagster_run_id = trigger_dagster_job(
            dagster_client=dagster_client,
            server_url=server_url,
            execution_config=execution_config,
            version_name=version_name,
            run_id=run.run_id,
        )
        run.status = RunStatus.STARTED
        run.dagster_run_id = dagster_run_id
    except Exception as e:
        run.status = RunStatus.FAILURE
        error_list = e.args[1]
        error_details = error_list[0]
        error_msg = f"Failed to trigger job: {error_details['message']}"

    db.commit()

    return run, error_msg


def trigger_dagster_job(
    dagster_client,
    server_url,
    execution_config: dict,
    version_name: str,
    run_id: UUID,
):
    # Trigger the Dagster job with Policy and Run IDs as inputs
    execution_config["resources"] = {
        "vulkan_run_config": {
            "config": {
                "run_id": str(run_id),
                "server_url": server_url,
            }
        }
    }
    dagster_run_id = trigger_run.trigger_dagster_job(
        dagster_client,
        version_name,
        DEFAULT_POLICY_NAME,
        execution_config,
    )
    return dagster_run_id

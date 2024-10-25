from uuid import UUID

from dagster_graphql import DagsterGraphQLClient
from sqlalchemy.orm import Session
from vulkan.core.run import RunStatus
from vulkan.dagster.policy import DEFAULT_POLICY_NAME
from vulkan.dagster.run_config import RUN_CONFIG_KEY
from vulkan_public.constants import POLICY_CONFIG_KEY

from vulkan_server import definitions
from vulkan_server.dagster import trigger_run
from vulkan_server.db import ConfigurationValue, PolicyVersion, Run
from vulkan_server.exceptions import (
    NotFoundException,
    UnhandledException,
    VariablesNotSetException,
)


def create_run(
    db: Session,
    dagster_client: DagsterGraphQLClient,
    server_url: str,
    policy_version_id: str,
    project_id: str,
    input_data: dict,
    run_config_variables: dict[str, str],
) -> Run:
    version = (
        db.query(PolicyVersion)
        .filter_by(
            policy_version_id=policy_version_id, project_id=project_id, archived=False
        )
        .first()
    )
    if version is None:
        msg = f"Policy version {policy_version_id} not found"
        raise NotFoundException(msg)

    policy_config_variables = _get_policy_config_variables(
        db, policy_version_id=policy_version_id, variables=version.variables
    )

    config_variables, missing = _merge_config_variables(
        run_config=run_config_variables,
        policy_config=policy_config_variables,
        required=version.variables,
    )
    if len(missing) > 0:
        raise VariablesNotSetException(f"Mandatory variables not set: {missing}")

    run, error_msg = launch_run(
        dagster_client=dagster_client,
        server_url=server_url,
        input_data=input_data,
        config_variables=config_variables,
        policy_version_id=version.policy_version_id,
        version_name=definitions.version_name(
            version.policy_id, version.policy_version_id
        ),
        db=db,
        project_id=project_id,
    )
    if run.status == RunStatus.FAILURE:
        raise UnhandledException(f"Failed to launch run: {error_msg}")

    return run


def _get_policy_config_variables(
    db: Session, policy_version_id: str, variables: list[str] | None
) -> dict[str, str]:
    if variables is None or len(variables) == 0:
        return {}

    results = (
        db.query(ConfigurationValue)
        .filter(
            (ConfigurationValue.policy_version_id == policy_version_id)
            & (ConfigurationValue.name.in_(variables))
        )
        .all()
    )
    return {v.name: v.value for v in results}


def _merge_config_variables(
    run_config: dict[str, str], policy_config: dict[str, str], required: list[str]
) -> tuple[dict[str, str], set[str]]:
    variables = policy_config.copy()
    variables.update(run_config)

    if not required:
        return variables, set()

    missing_variables = set(required) - set(variables.keys())
    return variables, missing_variables


def launch_run(
    dagster_client,
    server_url: str,
    policy_version_id: UUID,
    version_name: str,
    db: Session,
    project_id: str,
    input_data: dict,
    config_variables: dict[str, str] = None,
):
    if config_variables is None:
        config_variables = {}

    run = Run(
        policy_version_id=policy_version_id,
        status=RunStatus.PENDING,
        project_id=project_id,
    )
    db.add(run)
    db.commit()

    error_msg = ""
    # TODO: We should separate dagster and core db functionality to ensure its
    # easy to migrate to other execution engines.
    try:
        dagster_run_id = trigger_dagster_job(
            dagster_client=dagster_client,
            server_url=server_url,
            input_data=input_data,
            config_variables=config_variables,
            version_name=version_name,
            run_id=run.run_id,
        )
        run.status = RunStatus.STARTED
        run.dagster_run_id = dagster_run_id
    except Exception as e:
        run.status = RunStatus.FAILURE
        error_msg = f"Failed to trigger job: {str(e)}"
        # error_list = e.args[1]
        # error_details = error_list[0]
        # error_msg = f"Failed to trigger job: {error_details['message']}"

    db.commit()

    return run, error_msg


def trigger_dagster_job(
    dagster_client,
    server_url,
    version_name: str,
    run_id: UUID,
    input_data: dict,
    config_variables: dict[str, str],
):
    execution_config = {
        "ops": {"input_node": {"config": input_data}},
        "resources": {
            RUN_CONFIG_KEY: {
                "config": {
                    "run_id": str(run_id),
                    "server_url": server_url,
                }
            },
            POLICY_CONFIG_KEY: {"config": {"variables": config_variables}},
        },
    }

    dagster_run_id = trigger_run.trigger_dagster_job(
        dagster_client,
        version_name,
        DEFAULT_POLICY_NAME,
        execution_config,
    )
    return dagster_run_id

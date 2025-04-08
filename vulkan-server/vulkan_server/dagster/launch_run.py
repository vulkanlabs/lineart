from dataclasses import dataclass
from uuid import UUID

from dagster_graphql import DagsterGraphQLClient
from numpy.random import choice
from sqlalchemy.orm import Session
from vulkan_public.constants import POLICY_CONFIG_KEY

from vulkan.core.run import RunStatus
from vulkan.dagster.policy import DEFAULT_POLICY_NAME
from vulkan.dagster.run_config import RUN_CONFIG_KEY
from vulkan_server import definitions
from vulkan_server.config_variables import resolve_config_variables_from_id
from vulkan_server.dagster import trigger_run
from vulkan_server.db import PolicyVersion, Run
from vulkan_server.exceptions import (
    NotFoundException,
    UnhandledException,
    VariablesNotSetException,
)
from vulkan_server.logger import init_logger
from vulkan_server.schemas import PolicyAllocationStrategy

logger = init_logger("run_launcher")


def allocate_runs(
    db: Session,
    dagster_client: DagsterGraphQLClient,
    server_url: str,
    input_data: dict,
    run_group_id: UUID,
    allocation_strategy: PolicyAllocationStrategy,
):
    shadow = []

    if allocation_strategy.shadow is not None:
        for policy_version_id in allocation_strategy.shadow:
            run = Run(
                policy_version_id=policy_version_id,
                status=RunStatus.PENDING,
                run_group_id=run_group_id,
            )
            db.add(run)
            db.commit()
            shadow.append(run.run_id)

    opts = [opt.policy_version_id for opt in allocation_strategy.choice]
    freq = [opt.frequency / 1000 for opt in allocation_strategy.choice]
    policy_version_id = choice(opts, p=freq)

    main = create_run(
        db=db,
        dagster_client=dagster_client,
        server_url=server_url,
        input_data=input_data,
        run_group_id=run_group_id,
        policy_version_id=policy_version_id,
    )
    return {"main": main.run_id, "shadow": shadow}


def create_run(
    db: Session,
    dagster_client: DagsterGraphQLClient,
    server_url: str,
    input_data: dict,
    policy_version_id: str,
    run_group_id: UUID | None = None,
    run_config_variables: dict[str, str] | None = None,
):
    launcher = DagsterRunLauncher(
        db=db,
        dagster_client=dagster_client,
        server_url=server_url,
    )
    return launcher.create_run(
        input_data=input_data,
        run_group_id=run_group_id,
        policy_version_id=policy_version_id,
        run_config_variables=run_config_variables,
    )


def launch_run(
    db: Session,
    dagster_client: DagsterGraphQLClient,
    server_url: str,
    run: Run,
    input_data: dict,
    run_config_variables: dict[str, str] | None = None,
):
    launcher = DagsterRunLauncher(
        db=db,
        dagster_client=dagster_client,
        server_url=server_url,
    )
    return launcher.launch_run(
        run=run,
        input_data=input_data,
        run_config_variables=run_config_variables,
    )


@dataclass
class LaunchConfig:
    name: str
    variables: dict[str, str]


class DagsterRunLauncher:
    def __init__(
        self,
        db: Session,
        dagster_client: DagsterGraphQLClient,
        server_url: str,
    ):
        self.db = db
        self.server_url = server_url
        self.dagster_client = dagster_client

    def create_run(
        self,
        input_data: dict,
        policy_version_id: str,
        run_group_id: UUID | None = None,
        run_config_variables: dict[str, str] | None = None,
    ) -> Run:
        """Create and launch a run."""
        config = self._get_launch_config(
            policy_version_id=policy_version_id,
            run_config_variables=run_config_variables,
        )

        run = Run(
            policy_version_id=policy_version_id,
            status=RunStatus.PENDING,
            run_group_id=run_group_id,
        )
        self.db.add(run)
        self.db.commit()

        return self._trigger_job(
            run=run,
            config=config,
            input_data=input_data,
        )

    def launch_run(
        self,
        run: Run,
        input_data: dict,
        run_config_variables: dict[str, str] | None = None,
    ) -> Run:
        """Launch a run that has already been created."""
        config = self._get_launch_config(
            policy_version_id=run.policy_version_id,
            run_config_variables=run_config_variables,
        )
        return self._trigger_job(
            run=run,
            config=config,
            input_data=input_data,
        )

    def _get_launch_config(
        self,
        policy_version_id: str,
        run_config_variables: dict[str, str] | None = None,
    ) -> LaunchConfig:
        version = (
            self.db.query(PolicyVersion)
            .filter_by(
                policy_version_id=policy_version_id,
                archived=False,
            )
            .first()
        )
        if version is None:
            msg = f"Policy version {policy_version_id} not found"
            raise NotFoundException(msg)

        config_variables, missing = resolve_config_variables_from_id(
            db=self.db,
            policy_version_id=policy_version_id,
            required_variables=version.variables,
            run_config_variables=run_config_variables,
        )
        if len(missing) > 0:
            raise VariablesNotSetException(f"Mandatory variables not set: {missing}")

        return LaunchConfig(
            name=definitions.version_name(policy_version_id),
            variables=config_variables,
        )

    def _trigger_job(
        self,
        run: Run,
        config: LaunchConfig,
        input_data: dict,
    ) -> Run:
        # TODO: We should separate dagster and core db functionality to ensure
        # its easy to migrate to other execution engines.
        try:
            dagster_run_id = trigger_dagster_job(
                dagster_client=self.dagster_client,
                server_url=self.server_url,
                input_data=input_data,
                config_variables=config.variables,
                version_name=config.name,
                run_id=run.run_id,
            )
            run.status = RunStatus.STARTED
            run.dagster_run_id = dagster_run_id
            self.db.commit()
        except Exception as e:
            run.status = RunStatus.FAILURE
            self.db.commit()
            raise UnhandledException(f"Failed to launch run: {str(e)}")

        return run


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
    logger.debug(f"Triggering job with config: {execution_config}")

    dagster_run_id = trigger_run.trigger_dagster_job(
        dagster_client,
        version_name,
        DEFAULT_POLICY_NAME,
        execution_config,
    )
    return dagster_run_id

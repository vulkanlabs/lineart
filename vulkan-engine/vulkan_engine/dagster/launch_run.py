import asyncio
from dataclasses import dataclass
from uuid import UUID

from dagster_graphql import DagsterGraphQLClient
from numpy.random import choice
from sqlalchemy import select
from sqlalchemy.orm import Session

from vulkan.constants import POLICY_CONFIG_KEY
from vulkan.core.run import RunStatus
from vulkan.runners.dagster.policy import DEFAULT_POLICY_NAME
from vulkan.runners.dagster.run_config import RUN_CONFIG_KEY
from vulkan_engine.config_variables import resolve_config_variables_from_id
from vulkan_engine.dagster import trigger_run
from vulkan_engine.db import Run, Workflow
from vulkan_engine.exceptions import (
    NotFoundException,
    RunPollingTimeoutException,
    UnhandledException,
    VariablesNotSetException,
)
from vulkan_engine.loaders.policy_version import PolicyVersionLoader
from vulkan_engine.logger import init_logger
from vulkan_engine.schemas import PolicyAllocationStrategy, RunResult

logger = init_logger("run_launcher")


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
        self.policy_version_loader = PolicyVersionLoader(db)

    def create_run(
        self,
        input_data: dict,
        policy_version_id: str,
        run_group_id: UUID | None = None,
        run_config_variables: dict[str, str] | None = None,
        project_id: str = None,
    ) -> Run:
        """Create and launch a run."""
        config = self._get_launch_config(
            policy_version_id=policy_version_id,
            project_id=project_id,
            run_config_variables=run_config_variables,
        )

        run = Run(
            policy_version_id=policy_version_id,
            status=RunStatus.PENDING,
            run_group_id=run_group_id,
            project_id=project_id,
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
        project_id: str,
        run_config_variables: dict[str, str] | None = None,
    ) -> LaunchConfig:
        version = self.policy_version_loader.get_policy_version(
            policy_version_id,
            project_id=project_id,
        )
        if version is None:
            msg = f"Policy version {policy_version_id} not found"
            raise NotFoundException(msg)

        config_variables, missing = resolve_config_variables_from_id(
            db=self.db,
            policy_version_id=policy_version_id,
            required_variables=version.workflow.variables,
            run_config_variables=run_config_variables,
        )
        if len(missing) > 0:
            raise VariablesNotSetException(f"Mandatory variables not set: {missing}")

        return LaunchConfig(
            name=str(version.workflow_id),
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


def allocate_runs(
    db: Session,
    launcher: DagsterRunLauncher,
    input_data: dict,
    run_group_id: UUID,
    allocation_strategy: PolicyAllocationStrategy,
    project_id: str = None,
):
    shadow = []

    if allocation_strategy.shadow is not None:
        for policy_version_id in allocation_strategy.shadow:
            run = Run(
                policy_version_id=policy_version_id,
                status=RunStatus.PENDING,
                run_group_id=run_group_id,
                project_id=project_id,
            )
            db.add(run)
            db.commit()
            shadow.append(run.run_id)

    opts = [opt.policy_version_id for opt in allocation_strategy.choice]
    freq = [opt.frequency / 1000 for opt in allocation_strategy.choice]
    policy_version_id = choice(opts, p=freq)

    main = launcher.create_run(
        input_data=input_data,
        run_group_id=run_group_id,
        policy_version_id=policy_version_id,
        project_id=project_id,
    )
    return {"main": main.run_id, "shadow": shadow}


MIN_POLLING_INTERVAL_MS = 500
MAX_POLLING_TIMEOUT_MS = 300000


async def get_run_result(
    db: Session, run_id: str, polling_interval_ms: int, polling_timeout_ms: int
) -> RunResult:
    """Poll the database for the run result.

    This is a blocking function that will wait for the run to complete
    or timeout after a certain period.
    """

    def clip(value):
        return max(min(value, MAX_POLLING_TIMEOUT_MS), MIN_POLLING_INTERVAL_MS)

    elapsed = 0
    completed = False
    run_obj: Run | None = None

    polling_interval = clip(polling_interval_ms) / 1000
    polling_timeout = clip(polling_timeout_ms) / 1000

    while elapsed < polling_timeout:
        if run_obj:
            # Clear the database cache to ensure we get the latest run status
            db.expire(run_obj)

        run_obj = db.execute(select(Run).where(Run.run_id == run_id)).scalars().first()
        if run_obj.status in (RunStatus.SUCCESS, RunStatus.FAILURE):
            completed = True
            break

        await asyncio.sleep(polling_interval)
        elapsed += polling_interval

    if not completed:
        raise RunPollingTimeoutException(
            f"Run {run_id} timed out after {polling_timeout} seconds. "
            "Check the run logs for more details."
        )

    return RunResult(
        run_id=run_obj.run_id,
        status=run_obj.status,
        result=run_obj.result,
        run_metadata=run_obj.run_metadata,
    )

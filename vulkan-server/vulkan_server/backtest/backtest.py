import json
from uuid import UUID

from sqlalchemy.orm import Session

from vulkan_server.config_variables import resolve_config_variables
from vulkan_server.db import BeamWorkspace, WorkspaceStatus
from vulkan_server.logger import init_logger

logger = init_logger("backfill_launcher")


def resolve_backtest_envs(
    environments: list[dict[str, str]],
    policy_version_defaults: dict[str, str],
    required_variables: list[str],
) -> list[dict[str, str]]:
    merged_configs = []
    for env in environments:
        merged_variables, missing = resolve_config_variables(
            run_config_variables=env,
            policy_version_defaults=policy_version_defaults,
            required_variables=required_variables,
        )
        if len(missing) > 0:
            raise ValueError(
                f"Incomplete environment {json.dumps(env)}."
                f"Mandatory variables not set: {missing}"
            )
        merged_configs.append(merged_variables)

    if len(merged_configs) == 0:
        merged_configs = [{}]

    return merged_configs


def ensure_beam_workspace(
    policy_version_id: UUID,
    db: Session,
) -> BeamWorkspace:
    workspace = (
        db.query(BeamWorkspace).filter_by(policy_version_id=policy_version_id).first()
    )

    if workspace is None:
        msg = f"workspace: policy version {policy_version_id} failed"
        raise ValueError(msg)

    if workspace.status == WorkspaceStatus.CREATION_FAILED:
        raise ValueError(
            f"Workspace creation failed for policy version {policy_version_id}"
        )

    return workspace

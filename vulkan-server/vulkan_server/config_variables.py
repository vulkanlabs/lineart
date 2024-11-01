from sqlalchemy.orm import Session

from vulkan_server.db import ConfigurationValue


def resolve_config_variables(
    db: Session,
    policy_version_id: str,
    required_variables: list[str],
    run_config_variables: dict[str, str],
):
    policy_config_variables = _get_policy_config_variables(
        db,
        policy_version_id=policy_version_id,
        required_variables=required_variables,
    )

    config_variables, missing = _merge_config_variables(
        run_config=run_config_variables,
        policy_config=policy_config_variables,
        required_variables=required_variables,
    )
    return config_variables, missing


def _get_policy_config_variables(
    db: Session,
    policy_version_id: str,
    required_variables: list[str] | None,
) -> dict[str, str]:
    if required_variables is None or len(required_variables) == 0:
        return {}

    results = (
        db.query(ConfigurationValue)
        .filter(
            (ConfigurationValue.policy_version_id == policy_version_id)
            & (ConfigurationValue.name.in_(required_variables))
        )
        .all()
    )
    return {v.name: v.value for v in results}


def _merge_config_variables(
    run_config: dict[str, str] | None,
    policy_config: dict[str, str] | None,
    required_variables: list[str],
) -> tuple[dict[str, str], set[str]]:
    if run_config is None:
        run_config = {}
    if policy_config is None:
        policy_config = {}

    variables = policy_config.copy()
    variables.update(run_config)

    if not required_variables:
        return variables, set()

    missing_variables = set(required_variables) - set(variables.keys())
    return variables, missing_variables
    
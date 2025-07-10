from sqlalchemy.orm import Session

from vulkan_engine.db import ConfigurationValue


def resolve_config_variables_from_id(
    db: Session,
    policy_version_id: str,
    required_variables: list[str],
    run_config_variables: dict | None = None,
):
    policy_version_defaults = _get_policy_version_defaults(
        db,
        policy_version_id=policy_version_id,
        required_variables=required_variables,
    )

    return resolve_config_variables(
        policy_version_defaults=policy_version_defaults,
        run_config_variables=run_config_variables,
        required_variables=required_variables,
    )


def resolve_config_variables(
    policy_version_defaults: dict,
    required_variables: list[str],
    run_config_variables: dict | None = None,
) -> tuple[dict, set[str]]:
    config_variables, missing = _merge_config_variables(
        run_config_variables=run_config_variables,
        policy_version_defaults=policy_version_defaults,
        required_variables=required_variables,
    )
    return config_variables, missing


def _get_policy_version_defaults(
    db: Session,
    policy_version_id: str,
    required_variables: list[str] | None,
) -> dict:
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
    run_config_variables: dict | None,
    policy_version_defaults: dict | None,
    required_variables: list[str],
) -> tuple[dict, set[str]]:
    if run_config_variables is None:
        run_config_variables = {}
    if policy_version_defaults is None:
        policy_version_defaults = {}

    variables = policy_version_defaults.copy()
    variables.update(run_config_variables)

    if not required_variables:
        return variables, set()

    missing_variables = set(required_variables) - set(variables.keys())
    return variables, missing_variables

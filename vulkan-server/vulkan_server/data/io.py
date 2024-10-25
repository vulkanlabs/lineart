from vulkan_public.schemas import (
    CachingOptions,
    CachingTTL,
    DataSourceCreate,
    EnvVarConfig,
    RequestOptions,
    RetryPolicy,
)

from vulkan_server import schemas
from vulkan_server.db import DataSource


class DataSourceModelSerializer:
    @staticmethod
    def serialize(config: DataSourceCreate, project_id: str) -> DataSource:
        variables = extract_env_vars(config)
        return DataSource(
            project_id=project_id,
            name=config.name,
            description=config.description,
            keys=config.keys,
            request_url=config.request.url,
            request_method=config.request.method,
            request_headers=_parse_config(config.request.headers),
            request_params=_parse_config(config.request.params),
            request_timeout=config.request.timeout,
            caching_enabled=config.caching.enabled,
            caching_ttl=calculate_ttl(config.caching.ttl),
            retry_max_retries=config.retry.max_retries,
            retry_backoff_factor=config.retry.backoff_factor,
            retry_status_forcelist=config.retry.status_forcelist,
            config_metadata=config.metadata,
            variables=variables,
        )

    @staticmethod
    def deserialize(data: DataSource) -> schemas.DataSource:
        return schemas.DataSource(
            data_source_id=data.data_source_id,
            project_id=data.project_id,
            name=data.name,
            keys=data.keys,
            request=RequestOptions(
                url=data.request_url,
                method=data.request_method,
                headers=data.request_headers,
                params=data.request_params,
                timeout=data.request_timeout,
            ),
            caching=CachingOptions(
                enabled=data.caching_enabled,
                ttl=data.caching_ttl,
            ),
            retry=RetryPolicy(
                max_retries=data.retry_max_retries,
                backoff_factor=data.retry_backoff_factor,
                status_forcelist=data.retry_status_forcelist,
            ),
            description=data.description,
            metadata=data.config_metadata,
            variables=data.variables,
            archived=data.archived,
            created_at=data.created_at,
            last_updated_at=data.last_updated_at,
        )


def calculate_ttl(ttl: CachingTTL | int | None) -> int | None:
    if isinstance(ttl, int):
        return ttl
    if ttl is None:
        return None
    return ttl.days * 86400 + ttl.hours * 3600 + ttl.minutes * 60 + ttl.seconds


def extract_env_vars(config: DataSourceCreate) -> list[str]:
    env = []

    if config.request.headers:
        env += _extract_env_vars(config.request.headers)

    if config.request.params:
        env += _extract_env_vars(config.request.params)

    return env


def _extract_env_vars(config: dict) -> list[str]:
    return [v.env for v in config.values() if isinstance(v, EnvVarConfig)]


def _parse_config(config: dict) -> dict:
    for key, value in config.items():
        if isinstance(value, EnvVarConfig):
            config[key] = value.model_dump()
    return config

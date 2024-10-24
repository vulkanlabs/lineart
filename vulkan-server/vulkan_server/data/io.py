from vulkan_public.schemas import (
    CachingOptions,
    CachingTTL,
    RequestOptions,
    RetryPolicy,
)

from vulkan_server import schemas
from vulkan_server.db import DataSource


class DataSourceModelSerializer:
    @staticmethod
    def serialize(config: schemas.DataSourceCreate, project_id: str) -> DataSource:
        return DataSource(
            project_id=project_id,
            name=config.name,
            description=config.description,
            keys=config.keys,
            request_url=config.request.url,
            request_method=config.request.method,
            request_headers=config.request.headers,
            request_params=config.request.params,
            request_timeout=config.request.timeout,
            caching_enabled=config.caching.enabled,
            caching_ttl=calculate_ttl(config.caching.ttl),
            retry_max_retries=config.retry.max_retries,
            retry_backoff_factor=config.retry.backoff_factor,
            retry_status_forcelist=config.retry.status_forcelist,
            config_metadata=config.metadata,
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

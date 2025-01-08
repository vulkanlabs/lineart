from vulkan_public.schemas import CachingOptions, CachingTTL, DataSourceSpec

from vulkan_server import schemas
from vulkan_server.db import DataSource


class DataSourceModelSerializer:
    @staticmethod
    def serialize(config: DataSourceSpec, project_id: str) -> DataSource:
        variables = config.extract_env_vars()
        return DataSource(
            project_id=project_id,
            name=config.name,
            description=config.description,
            keys=config.keys,
            source=config.source.model_dump(),
            caching_enabled=config.caching.enabled,
            caching_ttl=calculate_ttl(config.caching.ttl),
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
            source=DataSourceSpec.model_validate(data.source),
            caching=CachingOptions(
                enabled=data.caching_enabled,
                ttl=data.caching_ttl,
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

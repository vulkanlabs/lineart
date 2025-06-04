from pydantic import BaseModel, Field

from vulkan.data_source import (
    HTTPSource,
    LocalFileSource,
    RegisteredFileSource,
)


class CachingTTL(BaseModel):
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: int = 0


class CachingOptions(BaseModel):
    enabled: bool = False
    ttl: CachingTTL | int | None = None

    def calculate_ttl(self) -> int | None:
        ttl = self.ttl
        if isinstance(ttl, int):
            return ttl
        if ttl is None:
            return None
        return ttl.days * 86400 + ttl.hours * 3600 + ttl.minutes * 60 + ttl.seconds


class DataSourceSpec(BaseModel):
    name: str
    source: HTTPSource | LocalFileSource | RegisteredFileSource
    caching: CachingOptions = CachingOptions()
    description: str | None = None
    metadata: dict | None = None

    def extract_env_vars(self) -> list[str]:
        return self.source.extract_env_vars()

    def extract_runtime_params(self) -> list[str]:
        return self.source.extract_runtime_params()


class BacktestOptions(BaseModel):
    target_column: str
    target_type: str
    environments: list[dict]
    categorical_columns: list[str] | None = None
    datetime_column: str | None = None


class PolicyRunPartition(BaseModel):
    policy_version_id: str
    frequency: int = Field(gt=0, le=1000)


class PolicyAllocationStrategy(BaseModel):
    choice: list[PolicyRunPartition]
    shadow: list[str] | None = None

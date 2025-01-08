from abc import ABC, abstractmethod

from pydantic import BaseModel

BaseType = str | int | float | bool


class SourceSpecBase(ABC):
    @abstractmethod
    def extract_env_vars(self) -> dict:
        pass


class EnvVarConfig(BaseModel):
    env: BaseType | list[BaseType]


ConfigurableMapping = dict[str, BaseType | list[BaseType] | EnvVarConfig]


class CachingTTL(BaseModel):
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: int = 0


class CachingOptions(BaseModel):
    enabled: bool = False
    ttl: CachingTTL | int | None = None


class RetryPolicy(BaseModel):
    max_retries: int
    backoff_factor: float | None = None
    status_forcelist: list[int] | None = None


class HTTPSource(BaseModel, SourceSpecBase):
    url: str
    method: str = "GET"
    headers: ConfigurableMapping | None = dict()
    params: ConfigurableMapping | None = dict()
    body_schema: dict | None = None
    timeout: int | None = None
    retry: RetryPolicy | None = RetryPolicy(max_retries=1)

    def extract_env_vars(self) -> list[str]:
        env = []
        if self.headers:
            env += _extract_env_vars(self.headers)
        if self.params:
            env += _extract_env_vars(self.params)

        return env


class RegisteredFileSource(BaseModel, SourceSpecBase):
    file_id: str

    def extract_env_vars(self) -> list[str]:
        return []


class LocalFileSource(BaseModel):
    path: str

    def extract_env_vars(self) -> list[str]:
        return []


def _extract_env_vars(config: dict) -> list[str]:
    return [v.env for v in config.values() if isinstance(v, EnvVarConfig)]


class DataSourceSpec(BaseModel):
    name: str
    keys: list[str]
    source: HTTPSource | LocalFileSource | RegisteredFileSource
    caching: CachingOptions
    description: str | None = None
    metadata: dict | None = None

    def extract_env_vars(self) -> list[str]:
        return self.source.extract_env_vars()


class BacktestOptions(BaseModel):
    target_column: str
    target_type: str
    environments: list[dict]
    categorical_columns: list[str] | None = None
    datetime_column: str | None = None

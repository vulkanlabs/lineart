from pydantic import BaseModel

BaseType = str | int | float | bool


class EnvVarConfig(BaseModel):
    env: BaseType | list[BaseType]


ConfigurableMapping = dict[str, BaseType | list[BaseType] | EnvVarConfig]


class RequestOptions(BaseModel):
    url: str
    method: str = "GET"
    headers: ConfigurableMapping | None = None
    params: ConfigurableMapping | None = None
    body_schema: dict | None = None
    timeout: int | None = None


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


class DataSourceCreate(BaseModel):
    name: str
    keys: list[str]
    request: RequestOptions
    caching: CachingOptions
    retry: RetryPolicy | None = None
    description: str | None = None
    metadata: dict | None = None

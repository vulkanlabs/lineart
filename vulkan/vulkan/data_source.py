from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel

BaseType = str | int | float | bool


class EnvVarConfig(BaseModel):
    env: str


class RunTimeParam(BaseModel):
    param: str


ConfigurableMapping = dict[str, BaseType | list[BaseType] | EnvVarConfig | RunTimeParam]


class DataSourceType(Enum):
    HTTP = "http"
    LOCAL_FILE = "local_file"
    REGISTERED_FILE = "registered_file"


class SourceSpecBase(ABC):
    @abstractmethod
    def extract_env_vars(self) -> dict:
        pass

    @abstractmethod
    def extract_runtime_params(self) -> dict:
        pass

    @property
    @abstractmethod
    def source_type(self) -> DataSourceType:
        pass


class RegisteredFileSource(BaseModel, SourceSpecBase):
    file_id: str
    path: str | None = None

    def extract_env_vars(self) -> list[str]:
        return []

    def extract_runtime_params(self) -> list[str]:
        return []

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.REGISTERED_FILE


class LocalFileSource(BaseModel):
    path: str

    def extract_env_vars(self) -> list[str]:
        return []

    def extract_runtime_params(self) -> list[str]:
        return []

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.LOCAL_FILE


class RetryPolicy(BaseModel):
    max_retries: int
    backoff_factor: float | None = None
    status_forcelist: list[int] | None = None


class ResponseType(Enum):
    JSON = "JSON"
    XML = "XML"
    CSV = "CSV"
    PLAIN_TEXT = "PLAIN_TEXT"


class HTTPSource(BaseModel, SourceSpecBase):
    url: str
    method: str = "GET"
    headers: ConfigurableMapping | None = dict()
    params: ConfigurableMapping | None = dict()
    body: ConfigurableMapping | None = dict()
    timeout: int | None = None
    retry: RetryPolicy | None = RetryPolicy(max_retries=1)
    response_type: str | None = ResponseType.PLAIN_TEXT.value

    def extract_env_vars(self) -> list[str]:
        env_vars = []
        for spec in [self.headers, self.params, self.body]:
            if spec:
                env_vars += _extract_env_vars(spec)
        return env_vars

    def extract_runtime_params(self) -> list[str]:
        params = []
        for spec in [self.headers, self.params, self.body]:
            if spec:
                params += [
                    v.param for v in spec.values() if isinstance(v, RunTimeParam)
                ]
        return params

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.HTTP


def _extract_env_vars(config: dict) -> list[str]:
    return [v.env for v in config.values() if isinstance(v, EnvVarConfig)]

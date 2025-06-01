from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel

BaseType = str | int | float | bool


class EnvVarConfig(BaseModel):
    env: str


class RunTimeParam(BaseModel):
    param: str


ParameterType = BaseType | list[BaseType] | EnvVarConfig | RunTimeParam
ConfigurableMapping = dict[str, ParameterType]


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
    path_params: list[ParameterType] | None = None
    query_params: ConfigurableMapping | None = dict()
    body: ConfigurableMapping | None = dict()
    timeout: int | None = None
    retry: RetryPolicy | None = RetryPolicy(max_retries=1)
    response_type: str | None = ResponseType.PLAIN_TEXT.value

    def extract_env_vars(self) -> list[str]:
        env_vars = []
        if self.path_params is not None:
            env_vars += [v.env for v in self.path_params if isinstance(v, EnvVarConfig)]
        for spec in [self.headers, self.query_params, self.body]:
            if spec:
                env_vars += _extract_env_vars(spec)
        return env_vars

    def extract_runtime_params(self) -> list[str]:
        params = []
        if self.path_params is not None:
            params += [v for v in self.path_params if isinstance(v, RunTimeParam)]
        for spec in [self.headers, self.query_params, self.body]:
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

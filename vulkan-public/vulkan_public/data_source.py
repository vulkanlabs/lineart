from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel

BaseType = str | int | float | bool


class EnvVarConfig(BaseModel):
    env: BaseType | list[BaseType]


ConfigurableMapping = dict[str, BaseType | list[BaseType] | EnvVarConfig]


class DataSourceType(Enum):
    HTTP = "http"
    LOCAL_FILE = "local_file"
    REGISTERED_FILE = "registered_file"


class SourceSpecBase(ABC):
    @abstractmethod
    def extract_env_vars(self) -> dict:
        pass

    @property
    @abstractmethod
    def source_type(self) -> DataSourceType:
        pass


class RegisteredFileSource(BaseModel, SourceSpecBase):
    file_id: str
    file_path: str | None = None

    def extract_env_vars(self) -> list[str]:
        return []

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.REGISTERED_FILE


class LocalFileSource(BaseModel):
    path: str

    def extract_env_vars(self) -> list[str]:
        return []

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.LOCAL_FILE


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

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.HTTP


def _extract_env_vars(config: dict) -> list[str]:
    return [v.env for v in config.values() if isinstance(v, EnvVarConfig)]

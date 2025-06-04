from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel

from vulkan.connections import HTTPConfig
from vulkan.node_config import (
    extract_env_vars,
    extract_env_vars_from_string,
    extract_runtime_params,
    extract_runtime_params_from_string,
)


class DataSourceType(Enum):
    HTTP = "http"
    LOCAL_FILE = "local_file"
    REGISTERED_FILE = "registered_file"


class SourceSpecBase(ABC):
    @abstractmethod
    def extract_env_vars(self) -> list[str]:
        pass

    @abstractmethod
    def extract_runtime_params(self) -> list[str]:
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


class HTTPSource(HTTPConfig, SourceSpecBase):
    def extract_env_vars(self) -> list[str]:
        env_vars = extract_env_vars_from_string(self.url)
        for spec in [self.headers, self.params, self.body]:
            if spec is not None:
                env_vars += extract_env_vars(spec)
        return env_vars

    def extract_runtime_params(self) -> list[str]:
        params = extract_runtime_params_from_string(self.url)
        for spec in [self.headers, self.params, self.body]:
            if spec is not None:
                params += extract_runtime_params(spec)
        return params

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.HTTP

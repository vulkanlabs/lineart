from typing import Any, TypeAlias

from pydantic import BaseModel

from vulkan.spec.dependency import Dependency


class BaseNodeMetadata(BaseModel):
    def to_dict(self) -> dict[str, Any]:
        """Convert the metadata to a dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Any:
        """Load the metadata from a dictionary."""
        return cls.model_validate(data)


class InputNodeMetadata(BaseNodeMetadata):
    schema: dict[str, str]


class BranchNodeMetadata(BaseNodeMetadata):
    choices: list[str]
    source_code: str


class TransformNodeMetadata(BaseNodeMetadata):
    source_code: str


class TerminateNodeMetadata(BaseNodeMetadata):
    return_status: str
    return_metadata: dict[str, Dependency] | None = None


class DataInputNodeMetadata(BaseNodeMetadata):
    data_source: str
    parameters: dict[str, Any] | None = None


class PolicyNodeMetadata(BaseNodeMetadata):
    policy_id: str


class ConnectionNodeMetadata(BaseNodeMetadata):
    url: str
    method: str = "GET"
    headers: dict[str, Any] | None = None
    path_params: list[Any] | None = None
    query_params: dict[str, Any] | None = None
    body: dict[str, Any] | None = None
    timeout: int | None = None
    retry_max_retries: int = 1
    response_type: str = "JSON"


NodeMetadata: TypeAlias = (
    InputNodeMetadata
    | BranchNodeMetadata
    | TransformNodeMetadata
    | TerminateNodeMetadata
    | DataInputNodeMetadata
    | PolicyNodeMetadata
    | ConnectionNodeMetadata
)

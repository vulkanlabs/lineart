from typing import Any, TypeAlias

from pydantic import BaseModel


class BaseNodeMetadata(BaseModel):
    def to_dict(self) -> dict[str, Any]:
        """Convert the metadata to a dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> None:
        """Load the metadata from a dictionary."""
        return cls.model_validate(data)


class InputNodeMetadata(BaseNodeMetadata):
    schema: dict[str, str]


class BranchNodeMetadata(BaseNodeMetadata):
    choices: list[str]
    func: Any | None
    source_code: str | None
    function_code: str


class TransformNodeMetadata(BaseNodeMetadata):
    func: Any | None
    source_code: str | None
    function_code: str


class TerminateNodeMetadata(BaseNodeMetadata):
    return_status: str


class DataInputNodeMetadata(BaseNodeMetadata):
    data_source: str


class PolicyNodeMetadata(BaseNodeMetadata):
    policy_definition: dict


NodeMetadata: TypeAlias = (
    InputNodeMetadata
    | BranchNodeMetadata
    | TransformNodeMetadata
    | TerminateNodeMetadata
    | DataInputNodeMetadata
    | PolicyNodeMetadata
)

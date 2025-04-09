from dataclasses import asdict, dataclass
from typing import Any


class BaseNodeMetadata(object):
    def to_dict(self) -> dict[str, Any]:
        """Convert the metadata to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> None:
        """Load the metadata from a dictionary."""
        return cls(**data)


@dataclass
class InputNodeMetadata(BaseNodeMetadata):
    schema: dict[str, str]


@dataclass
class BranchNodeMetadata(BaseNodeMetadata):
    choices: list[str]
    func: Any | None
    source_code: str | None
    function_code: str


@dataclass
class TransformNodeMetadata(BaseNodeMetadata):
    func: Any | None
    source_code: str | None
    function_code: str


@dataclass
class TerminateNodeMetadata(BaseNodeMetadata):
    return_status: str


@dataclass
class DataInputNodeMetadata(BaseNodeMetadata):
    data_source: str


@dataclass
class PolicyNodeMetadata(BaseNodeMetadata):
    policy_definition: Any


NodeMetadata = (
    InputNodeMetadata
    | BranchNodeMetadata
    | TransformNodeMetadata
    | TerminateNodeMetadata
    | DataInputNodeMetadata
    | PolicyNodeMetadata
)

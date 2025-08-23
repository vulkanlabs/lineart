from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel


class BaseNodeMetadata(BaseModel):
    def to_dict(
        self, mode: str | Literal["json", "python"] = "python"
    ) -> dict[str, Any]:
        """Convert the metadata to a dictionary."""
        return self.model_dump(mode=mode)

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
    parameters: dict[str, str] | None = None


class TerminateNodeMetadata(BaseNodeMetadata):
    return_status: str
    return_metadata: str | None = (
        None  # Generated from output_data for frontend compatibility
    )
    output_data: dict[str, str] | None = None  # Primary storage for SDK


class DataInputNodeMetadata(BaseNodeMetadata):
    data_source: str
    parameters: dict[str, Any] | None = None


class PolicyNodeMetadata(BaseNodeMetadata):
    policy_id: str


class ConnectionNodeMetadata(BaseNodeMetadata):
    url: str
    method: str = "GET"
    headers: dict[str, Any] | None = None
    params: dict[str, Any] | None = None
    body: dict[str, Any] | None = None
    timeout: int | None = None
    retry_max_retries: int = 1
    response_type: str = "JSON"


class DecisionType(Enum):
    IF = "if"
    ELSE_IF = "else-if"
    ELSE = "else"


class DecisionCondition(BaseModel):
    decision_type: DecisionType
    condition: str | None = None
    output: str


class DecisionNodeMetadata(BaseNodeMetadata):
    conditions: list[DecisionCondition]


class ComponentNodeMetadata(BaseNodeMetadata):
    component_name: str
    definition: dict | None = None
    parameters: dict | None = None

from abc import ABC, abstractmethod
from typing import Any


class NodeMetadata(ABC):
    @staticmethod
    @abstractmethod
    def entries() -> list[str]:
        """Return a list of all the attributes that should be serialized."""

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if k in self.entries()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NodeMetadata":
        missing_keys = set(cls.entries()) - set(data.keys())
        if missing_keys:
            raise ValueError(f"Missing keys: {missing_keys}")
        return cls(**data)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NodeMetadata):
            return False
        return self.__dict__ == other.__dict__


class InputNodeMetadata(NodeMetadata):
    def __init__(self, schema: dict[str, type]):
        self.schema = schema

    @staticmethod
    def entries() -> list[str]:
        return ["schema"]


class BranchNodeMetadata(NodeMetadata):
    def __init__(
        self,
        choices: list[str],
        function_code: str,
        source_code: str | None,
        func: bytes | None,
    ):
        self.choices = choices
        self.function_code = function_code
        self.func = func
        self.source_code = source_code

    @staticmethod
    def entries() -> list[str]:
        return ["choices", "func", "source_code", "function_code"]


class TransformNodeMetadata(NodeMetadata):
    def __init__(self, source: str):
        self.source = source

    @staticmethod
    def entries() -> list[str]:
        return ["source"]


class TerminateNodeMetadata(NodeMetadata):
    def __init__(self, return_status: str):
        self.return_status = return_status

    @staticmethod
    def entries() -> list[str]:
        return ["return_status"]


class DataInputNodeMetadata(NodeMetadata):
    def __init__(self, data_source: str):
        self.data_source = data_source

    @staticmethod
    def entries() -> list[str]:
        return ["data_source"]


class PolicyNodeMetadata(NodeMetadata):
    def __init__(self, policy_definition):
        self.policy_definition = policy_definition

    @staticmethod
    def entries() -> list[str]:
        return ["policy_definition"]

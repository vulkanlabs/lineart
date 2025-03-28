from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any

from vulkan_public.spec.dependency import Dependency
from vulkan_public.spec.nodes.metadata import (
    BranchNodeMetadata,
    DataInputNodeMetadata,
    InputNodeMetadata,
    NodeMetadata,
    PolicyNodeMetadata,
    TerminateNodeMetadata,
    TransformNodeMetadata,
)


class NodeType(Enum):
    TRANSFORM = "TRANSFORM"
    TERMINATE = "TERMINATE"
    BRANCH = "BRANCH"
    INPUT = "INPUT"
    DATA_INPUT = "DATA_INPUT"
    POLICY = "POLICY"


@dataclass(frozen=True)
class NodeDefinition:
    "Internal representation of a node."

    name: str
    node_type: str
    description: str | None = None
    dependencies: dict[str, Dependency] | None = None
    metadata: NodeMetadata | None = None

    _REQUIRED_KEYS = {"name", "node_type"}

    def __post_init__(self):
        if self.metadata is not None:
            if not isinstance(self.metadata, NodeMetadata):
                msg = (
                    f"Metadata must be of type NodeMetadata, got {type(self.metadata)}"
                )
                raise TypeError(msg)
        if self.dependencies is not None:
            assert all(
                isinstance(d, Dependency) for d in self.dependencies.values()
            ), "Dependencies must be of type Dependency"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NodeDefinition":
        missing_keys = cls._REQUIRED_KEYS - set(data.keys())
        if missing_keys:
            raise ValueError(f"Missing keys: {missing_keys}")

        metadata = data.get("metadata", None)
        if metadata is not None:
            node_type = NodeType(data["node_type"])
            if node_type == NodeType.TRANSFORM:
                metadata = TransformNodeMetadata.from_dict(metadata)
            elif node_type == NodeType.TERMINATE:
                metadata = TerminateNodeMetadata.from_dict(metadata)
            elif node_type == NodeType.BRANCH:
                metadata = BranchNodeMetadata.from_dict(metadata)
            elif node_type == NodeType.INPUT:
                metadata = InputNodeMetadata.from_dict(metadata)
            elif node_type == NodeType.DATA_INPUT:
                metadata = DataInputNodeMetadata.from_dict(metadata)
            elif node_type == NodeType.POLICY:
                metadata = PolicyNodeMetadata.from_dict(metadata)
            else:
                raise ValueError(f"Unknown node type: {node_type}")

        return cls(
            name=data["name"],
            node_type=data["node_type"],
            description=data.get("description"),
            dependencies=data.get("dependencies"),
            metadata=metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "node_type": self.node_type,
        }
        if self.description is not None:
            data["description"] = self.description
        if self.dependencies is not None:
            data["dependencies"] = self.dependencies
        if self.metadata is not None:
            data["metadata"] = self.metadata.to_dict()
        return data


class Node(ABC):
    """A node represents a step in a workflow.

    It can be thought of as a function that executes in an isolated environment.
    Each node represents a vertice in a DAG, and declares its dependencies,
    which are the edges in the graph.
    """

    def __init__(
        self,
        name: str,
        typ: NodeType,
        description: str | None = None,
        dependencies: dict[str, Dependency] | None = None,
        hierarchy: list[str] | None = None,
    ):
        """A node. This is an abstract class and should not be instantiated directly.

        Parameters
        ----------
        name : str
            The name of the node.
        typ : NodeType
            The type of the node. Determines the overall behavior of the node.
        description : str, optional
            A description of the node. Used for documentation purposes and
            shown in the user interface.
        dependencies : dict[str, Dependency], optional
            The dependencies of the node. A dictionary where the key is the name
            of the variable that will receive the data, and the value is the source.
            See `Dependency` for more information.

        """
        self._name = name
        self.description = description
        self.type = typ
        self._dependencies = dependencies if dependencies is not None else {}
        # TODO: here, we can enforce the typing of dependency specifications,
        # but this ends up making the API harder to use. We should consider
        # parsing the dependency specification from strings or tuples.
        if not isinstance(self._dependencies, dict):
            raise TypeError(f"Dependencies must be a dict, got: {dependencies}")
        if not all(isinstance(d, Dependency) for d in self._dependencies.values()):
            raise TypeError("Dependencies must be of type Dependency")

        self._hierarchy = hierarchy

    @abstractmethod
    def node_definition(self) -> NodeDefinition:
        pass

    @abstractmethod
    def from_dict(cls, spec: dict[str, Any]) -> "Node":
        pass

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> dict[str, Dependency]:
        return self._dependencies

    @property
    def hierarchy(self) -> list[str] | None:
        return self._hierarchy

    def add_hierarchy_level(self, level: str) -> "Node":
        hierarchy = self.hierarchy if self.hierarchy is not None else []
        hierarchy = [*hierarchy, level]

        n = deepcopy(self)
        n._hierarchy = hierarchy
        for dep in n.dependencies.values():
            dep.hierarchy = hierarchy

        return n

    @property
    def id(self) -> str:
        if self._hierarchy is None:
            return self.name
        return "-".join(self._hierarchy) + "." + self._name

    def node_dependencies(self) -> list[Dependency]:
        return list(self.dependencies.values())

    def to_dict(self) -> dict[str, Any]:
        return self.node_definition().to_dict()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Node):
            return False
        return self.node_definition() == other.node_definition()

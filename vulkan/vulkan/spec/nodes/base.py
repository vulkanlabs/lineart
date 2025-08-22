from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel

from vulkan.spec.dependency import Dependency, DependencyDict
from vulkan.spec.nodes.metadata import (
    BaseNodeMetadata,
    BranchNodeMetadata,
    ComponentNodeMetadata,
    ConnectionNodeMetadata,
    DataInputNodeMetadata,
    DecisionNodeMetadata,
    InputNodeMetadata,
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
    CONNECTION = "CONNECTION"
    DECISION = "DECISION"
    COMPONENT = "COMPONENT"


NODE_METADATA_TYPE_MAP = {
    NodeType.TRANSFORM: TransformNodeMetadata,
    NodeType.TERMINATE: TerminateNodeMetadata,
    NodeType.BRANCH: BranchNodeMetadata,
    NodeType.INPUT: InputNodeMetadata,
    NodeType.DATA_INPUT: DataInputNodeMetadata,
    NodeType.POLICY: PolicyNodeMetadata,
    NodeType.CONNECTION: ConnectionNodeMetadata,
    NodeType.DECISION: DecisionNodeMetadata,
    NodeType.COMPONENT: ComponentNodeMetadata,
}


class NodeDefinitionDict(BaseModel):
    """Dict representation of a NodeDefinition object."""

    name: str
    node_type: str
    dependencies: dict[str, DependencyDict] | None = None
    metadata: dict | None = None
    description: str | None = None
    hierarchy: list[str] | None = None


@dataclass()
class NodeDefinition:
    "Internal representation of a node."

    name: str
    node_type: str
    description: str | None = None
    dependencies: dict[str, DependencyDict] | None = None
    metadata: BaseNodeMetadata | None = None
    hierarchy: list[str] | None = None

    _REQUIRED_KEYS = {"name", "node_type"}

    def __post_init__(self):
        if self.metadata is not None:
            if not isinstance(self.metadata, BaseNodeMetadata):
                msg = f"Metadata must be an instance of ComponentNodeMetadata, got {type(self.metadata)}"
                raise TypeError(msg)
        if self.dependencies is not None:
            deps = {}
            for key, dep in self.dependencies.items():
                if isinstance(dep, Dependency):
                    deps[key] = dep
                else:
                    try:
                        dep = Dependency.from_dict(dep)
                        deps[key] = dep
                    except Exception as e:
                        msg = f"Error parsing dependency {key}: {e}"
                        raise ValueError(msg) from e
            self.dependencies = deps
            if not all(isinstance(d, Dependency) for d in self.dependencies.values()):
                msg = f"Dependencies must be of type Dependency: {self.dependencies}"
                raise ValueError(msg)

    @classmethod
    def from_dict(cls, data: NodeDefinitionDict) -> "NodeDefinition":
        missing_keys = cls._REQUIRED_KEYS - set(data.keys())
        if missing_keys:
            raise ValueError(f"Missing keys: {missing_keys}")

        metadata = data.get("metadata", None)
        if metadata is not None:
            node_type = NodeType(data["node_type"])
            metadata = NODE_METADATA_TYPE_MAP[node_type].from_dict(metadata)

        return cls(
            name=data["name"],
            node_type=data["node_type"],
            description=data.get("description"),
            dependencies=data.get("dependencies"),
            metadata=metadata,
            hierarchy=data.get("hierarchy"),
        )

    def to_dict(
        self, mode: str | Literal["json", "python"] = "python"
    ) -> NodeDefinitionDict:
        data: dict[str, Any] = {
            "name": self.name,
            "node_type": self.node_type,
        }
        if self.description is not None:
            data["description"] = self.description
        if self.dependencies is not None:
            data["dependencies"] = {
                key: d.to_dict() for key, d in self.dependencies.items()
            }
        if self.metadata is not None:
            data["metadata"] = self.metadata.to_dict(mode=mode)
        if self.hierarchy is not None:
            data["hierarchy"] = self.hierarchy
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
        if not isinstance(self._dependencies, dict):
            raise TypeError(f"Dependencies must be a dict, got: {dependencies}")
        if not all(isinstance(d, Dependency) for d in self._dependencies.values()):
            raise TypeError("Dependencies must be of type Dependency")

        self._hierarchy = hierarchy

    @abstractmethod
    def node_definition(self) -> NodeDefinition:
        pass

    @abstractmethod
    def from_dict(cls, spec: NodeDefinitionDict) -> "Node":
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

    @hierarchy.setter
    def hierarchy(self, hierarchy: list[str]):
        self._hierarchy = hierarchy

    @property
    def id(self) -> str:
        if self._hierarchy is None or len(self._hierarchy) == 0:
            return self.name
        return "-".join(self._hierarchy) + "." + self._name

    def node_dependencies(self) -> list[Dependency]:
        return list(self.dependencies.values())

    def to_dict(
        self, mode: str | Literal["json", "python"] = "python"
    ) -> NodeDefinitionDict:
        return self.node_definition().to_dict(mode)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Node):
            return False
        return self.node_definition() == other.node_definition()


class PolicyDefinitionDict(BaseModel):
    """Dict representation of a PolicyDefinition object."""

    nodes: list[NodeDefinitionDict]
    input_schema: dict[str, str]
    config_variables: list[str] | None = None
    output_callback: str | None = None

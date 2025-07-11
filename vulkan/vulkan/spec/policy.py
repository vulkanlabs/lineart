from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from pydantic import BaseModel

from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.graph import GraphDefinition
from vulkan.spec.nodes import (
    BranchNode,
    ConnectionNode,
    DataInputNode,
    DecisionNode,
    InputNode,
    TerminateNode,
    TransformNode,
)
from vulkan.spec.nodes.base import Node, NodeDefinition, NodeDefinitionDict, NodeType
from vulkan.spec.nodes.metadata import PolicyNodeMetadata


class PolicyDefinitionDict(BaseModel):
    """Dict representation of a PolicyDefinition object."""

    nodes: list[NodeDefinitionDict]
    input_schema: dict[str, str]
    config_variables: list[str] | None = None


@dataclass
class PolicyDefinition(GraphDefinition):
    """A policy definition specifies the workflow of a policy.

    A policy is composed of nodes  and the dependencies between them.
    Each node represents a step in the workflow, and can be
    thought of as a function that executes in an isolated environment.
    It receives data from its dependencies, and produces data that can be
    passed to other nodes.

    Dependencies are the main method to pass data between nodes.
    When a node depends on another, the output of the dependency is used
    as input to the node.

    Dependencies are specified per node, as a dictionary, where the key
    is the name of a variable that will receive the data, and the value
    specifies the source node.
    An example of a dependency is:
    `{"source_node_outputs": Dependency("source_node")}`
    In this case, the parameter `source_node_outputs` will receive the output
    of the `source_node` node.

    Parameters
    ----------
    nodes : list[Node]
        The nodes that compose the policy.
        Each node represents a step in the workflow, and can be thought of as
        a function that executes in an isolated environment.
    input_schema : dict[str, type]
        The input schema of the policy.
        It is a dictionary where the key is the name of the input parameter, and
        the value is the type of the parameter.
    output_callback : Callable, optional
        A callback that is called when the policy finishes execution.
        The callback receives the output of the policy as input.
    config_variables : list[str], optional
        The configuration variables that are used to parameterize policy.
        They provide a way to customize the behavior of the policy without
        changing the underlying logic.

    """

    nodes: list[Node]
    input_schema: dict[str, str]
    output_callback: Callable | None = None
    config_variables: list[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if self.output_callback is not None:
            if not callable(self.output_callback):
                raise ValueError("Output callback must be a callable")

        if self.config_variables:
            if not isinstance(self.config_variables, list) or not (
                all(isinstance(i, str) for i in self.config_variables)
            ):
                raise ValueError("config_variables must be a list of strings")

        for node in self.nodes:
            if node.name == INPUT_NODE:
                raise ValueError(f"Node name`{INPUT_NODE}` is reserved")

    def to_dict(
        self, mode: str | Literal["json", "python"] = "python"
    ) -> PolicyDefinitionDict:
        return {
            "nodes": [node.to_dict(mode) for node in self.nodes],
            "input_schema": self.input_schema,
            "output_callback": self.output_callback,
            "config_variables": self.config_variables,
        }

    @classmethod
    def from_dict(self, spec: PolicyDefinitionDict) -> "PolicyDefinition":
        nodes = [node_from_spec(node) for node in spec["nodes"]]

        return PolicyDefinition(
            nodes=nodes,
            input_schema=spec["input_schema"],
            output_callback=spec.get("output_callback", None),
            config_variables=spec.get("config_variables", []),
        )


class PolicyDefinitionNode(Node):
    """A node that represents a policy definition.
    Policy nodes are used to "invoke" policies from within other policies.
    They're used to insert additional metadata for the policy so that it
    can be appropriately connectied to the rest of the workflow.
    """

    def __init__(
        self,
        name: str,
        policy_id: str,
        description: str | None = None,
        dependencies: dict[str, Dependency] | None = None,
    ):
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.POLICY,
            dependencies=dependencies,
        )
        self.policy_id = policy_id

    def node_definition(self) -> NodeDefinition:
        metadata = PolicyNodeMetadata(policy_id=self.policy_id)
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.dependencies,
            metadata=metadata,
        )

    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "PolicyDefinitionNode":
        definition = NodeDefinition.from_dict(spec)
        if definition.node_type != NodeType.POLICY.value:
            raise ValueError(f"Expected NodeType.POLICY, got {definition.node_type}")
        if definition.metadata is None or definition.metadata.policy_id is None:
            raise ValueError("Missing policy metadata")

        return cls(
            name=definition.name,
            description=definition.description,
            dependencies=definition.dependencies,
            policy_id=definition.metadata.policy_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "node_type": self.type.value,
            "description": self.description,
            "dependencies": self.dependencies,
            "metadata": {
                "policy_definition": self.policy_id,
            },
        }


NODE_IMPLEMENTS = {
    NodeType.TRANSFORM: TransformNode,
    NodeType.TERMINATE: TerminateNode,
    NodeType.INPUT: InputNode,
    NodeType.DATA_INPUT: DataInputNode,
    NodeType.BRANCH: BranchNode,
    NodeType.POLICY: PolicyDefinitionNode,
    NodeType.CONNECTION: ConnectionNode,
    NodeType.DECISION: DecisionNode,
}


def node_from_spec(spec: dict[str, str]) -> Node:
    """Create a node from a specification dictionary.

    Parameters
    ----------
    spec : dict[str, str]
        The specification dictionary containing the node type and other parameters.

    Returns
    -------
    Node
        The created node instance.

    Raises
    ------
    ValueError
        If the node type is not recognized or if the specification is invalid.
    """
    node_type = spec.get("node_type")
    if node_type is None:
        raise ValueError("Missing node_type")

    node_type = NodeType(node_type)

    if node_type not in NODE_IMPLEMENTS:
        raise ValueError(f"Unknown node type: {node_type}")

    return NODE_IMPLEMENTS[node_type].from_dict(spec)

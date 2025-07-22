import builtins
from dataclasses import dataclass, field
from typing import Callable, Literal

from vulkan.spec.dependency import INPUT_NODE
from vulkan.spec.graph import GraphDefinition
from vulkan.spec.nodes import (
    BranchNode,
    ComponentNode,
    ConnectionNode,
    DataInputNode,
    DecisionNode,
    InputNode,
    PolicyDefinitionNode,
    TerminateNode,
    TransformNode,
)
from vulkan.spec.nodes.base import Node, NodeType, PolicyDefinitionDict


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
    hierarchy: list[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self._input_node = make_input_node(self.input_schema, self.hierarchy)

        for node in self.nodes:
            node.hierarchy = self.hierarchy
            for dep in node.dependencies.values():
                dep.hierarchy = self.hierarchy

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
    def from_dict(
        self,
        spec: PolicyDefinitionDict,
        hierarchy: list[str] | None = None,
    ) -> "PolicyDefinition":
        nodes = [node_from_spec(node) for node in spec["nodes"]]

        return PolicyDefinition(
            nodes=nodes,
            input_schema=spec["input_schema"],
            output_callback=spec.get("output_callback", None),
            config_variables=spec.get("config_variables", []),
            hierarchy=hierarchy,
        )

    @property
    def input_node(self) -> InputNode:
        return self._input_node

    @input_node.setter
    def input_node(self, input_node: InputNode):
        self._input_node = input_node


NODE_IMPLEMENTS = {
    NodeType.TRANSFORM: TransformNode,
    NodeType.TERMINATE: TerminateNode,
    NodeType.INPUT: InputNode,
    NodeType.DATA_INPUT: DataInputNode,
    NodeType.BRANCH: BranchNode,
    NodeType.POLICY: PolicyDefinitionNode,
    NodeType.CONNECTION: ConnectionNode,
    NodeType.DECISION: DecisionNode,
    NodeType.COMPONENT: ComponentNode,
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


def make_input_node(
    input_schema: dict[str, type | str],
    hierarchy: list[str] | None = None,
) -> InputNode:
    input_schema = _parse_input_schema(input_schema)
    return InputNode(
        name=INPUT_NODE,
        description="Input node",
        schema=input_schema,
        hierarchy=hierarchy,
    )


def _parse_input_schema(input_schema: dict[str, type | str]) -> dict[str, type | str]:
    """Parse the input schema to ensure that all types are valid."""
    parsed_schema = {}
    for key, value in input_schema.items():
        if isinstance(value, str):
            # If the type is a string, we assume it's a built-in type
            if hasattr(builtins, value):
                parsed_schema[key] = getattr(builtins, value)
            else:
                msg = f"Invalid type '{value}' for key '{key}'"
                raise ValueError(msg)
        elif isinstance(value, type):
            parsed_schema[key] = value
        else:
            msg = f"Invalid type for key '{key}': {type(value)}"
            raise ValueError(msg)
    return parsed_schema

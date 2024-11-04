from dataclasses import dataclass, field
from typing import Callable

from vulkan_public.spec.component import ComponentInstance
from vulkan_public.spec.dependency import INPUT_NODE
from vulkan_public.spec.graph import GraphDefinition
from vulkan_public.spec.nodes import Node, NodeType


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
    components : list[ComponentInstance], optional
        The components used in the policy.
        Components are reusable blocks of code that can be used in multiple
        policies. They are defined using a `ComponentDefinition`, and can be
        instantiated multiple times with different configurations.
    config_variables : list[str], optional
        The configuration variables that are used to parameterize policy.
        They provide a way to customize the behavior of the policy without
        changing the underlying logic.

    """

    nodes: list[Node]
    input_schema: dict[str, type]
    output_callback: Callable | None = None
    components: list[ComponentInstance] = field(default_factory=list)
    config_variables: list[str] = field(default_factory=list)

    def __post_init__(self):
        # TODO: Perform type checking with pydantic.
        if self.output_callback is not None:
            if not callable(self.output_callback):
                raise ValueError("Output callback must be a callable")

        if self.config_variables:
            if not isinstance(self.config_variables, list) or not (
                all(isinstance(i, str) for i in self.config_variables)
            ):
                raise ValueError("config_variables must be a list of strings")

        self.validate_nodes()

        nodes = {node.name: node.dependencies for node in self.nodes}
        nodes.update({c.config.name: c.config.dependencies for c in self.components})
        self.validate_node_dependencies(nodes)

    def validate_nodes(self):
        # TODO: we should assert that all leaves are terminate nodes
        terminate_nodes = [
            node for node in self.nodes if node.type == NodeType.TERMINATE
        ]
        if len(terminate_nodes) == 0:
            raise ValueError("No terminate node found in policy.")

        nodes = {node.name: node for node in self.nodes}
        components = {c.config.name: c.config for c in self.components}
        for node in self.nodes:
            for dependency in node.dependencies.values():
                if dependency.node in components or dependency.node == INPUT_NODE:
                    continue

                if nodes[dependency.node].type == NodeType.TERMINATE:
                    raise ValueError(
                        f"Node {node.name} depends on terminate node {dependency}"
                    )

from dataclasses import dataclass, field
from typing import Callable

from vulkan_public.spec.dependency import INPUT_NODE
from vulkan_public.spec.graph import GraphDefinition
from vulkan_public.spec.nodes.base import Node


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
    input_schema: dict[str, type]
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

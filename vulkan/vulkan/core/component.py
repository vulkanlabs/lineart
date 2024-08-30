from typing import Any

from .graph import Graph
from .nodes import Node, NodeFactory, NodeType, TransformNode, VulkanNodeDefinition
from .dependency import Dependency


class ComponentGraph(Node, Graph):
    def __init__(
        self,
        name: str,
        description: str,
        nodes: list[Node],
        input_schema: dict[str, type],
        dependencies: dict[str, Any],
    ):
        # TODO: match input_schema with dependencies
        # TODO: assert there aren't Terminate nodes in the component

        # TODO: insert component input node as internal node (when we have
        # the execution logic implemented in our core)

        nodes = _prefix_node_names(name, nodes)
        nodes = _update_node_dependencies(name, nodes)
        all_nodes = [_make_input_node(name, dependencies), *nodes]

        Node.__init__(
            self,
            name=name,
            description=description,
            typ=NodeType.COMPONENT,
            dependencies=dependencies,
        )
        Graph.__init__(self, nodes=all_nodes, input_schema=input_schema)

        # TODO: find output node
        self.output_node = _find_output_node(nodes)

    @property
    def input_node_name(self) -> str:
        return self.make_input_node_name(self.name)

    @property
    def output_node_name(self) -> str:
        return self.output_node.name

    @staticmethod
    def make_input_node_name(component_name: str) -> str:
        return f"{component_name}_input_node"

    @staticmethod
    def make_output_node_name(component_name: str) -> str:
        return f"{component_name}_output"

    def node_definition(self) -> VulkanNodeDefinition:
        return VulkanNodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.node_dependencies(),
            metadata={
                "nodes": {n.name: n.node_definition() for n in self.nodes},
            },
        )


def _make_input_node(name: str, dependencies: dict[str, Dependency]) -> list[Node]:
    def _input_fn(_, **kwargs: dict):
        inputs = {}
        for k, v in dependencies.items():
            if k not in kwargs.keys():
                raise ValueError(f"Missing input {k}")
            if v.key is not None:
                inputs[k] = kwargs[k][v.key]
            else:
                inputs[k] = kwargs[k]

        return inputs

    return TransformNode(
        name=ComponentGraph.make_input_node_name(name),
        description=f"Input node for Component {name}",
        func=_input_fn,
        dependencies=dependencies,
        hidden=True,
    )


def _prefix_node_names(prefix: str, nodes: list[Node]) -> list[Node]:
    _nodes = []
    for node in nodes:
        # TODO: quick fix. Refactor ASAP.
        node._name = f"{prefix}_{node.name}"
        _nodes.append(node)
    return _nodes


def _update_node_dependencies(name: str, nodes: list[Node]) -> list[Node]:
    _nodes = []
    for node in nodes:
        dependencies = {}
        for k, v in node.dependencies.items():
            if v.node == "input_node":
                dependencies[k] = Dependency(ComponentGraph.make_input_node_name(name))
            else:
                v.node = f"{name}_{v.node}"
                dependencies[k] = v
        node._dependencies = dependencies
        _nodes.append(node)
    return _nodes


def _find_output_node(nodes: list[Node]) -> Node:
    non_terminal_nodes = []

    for node in nodes:
        for dep in node.node_dependencies():
            if dep.node not in non_terminal_nodes:
                non_terminal_nodes.append(dep.node)

    for node in nodes:
        if node.name not in non_terminal_nodes:
            return node


class ComponentDefinition:
    def __init__(
        self,
        nodes: list[Node | NodeFactory],
        input_schema: dict[str, type],
        instance_params_schema: dict[str, type],
    ):
        self.nodes = nodes
        self.input_schema = input_schema
        self.instance_params_schema = instance_params_schema


class ComponentInstance:
    def __init__(self, name: str, version: str, config: dict[str, Any]):
        self.name = name
        self.version = version
        self.config = config

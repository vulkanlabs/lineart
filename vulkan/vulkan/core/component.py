from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from vulkan.core.dependency import Dependency
from vulkan.core.graph import Graph
from vulkan.core.nodes import Node, NodeType, TransformNode, VulkanNodeDefinition


@dataclass
class InstanceParam:
    name: str


@dataclass
class ComponentDefinition:
    nodes: list[Node]
    input_schema: dict[str, type]
    instance_params_schema: dict[str, type]


@dataclass
class ComponentInstanceConfig:
    name: str
    description: str
    dependencies: dict[str, Dependency]
    instance_params: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict) -> "ComponentInstanceConfig":
        return cls(
            name=data["name"],
            description=data["description"],
            dependencies={
                k: Dependency.from_dict(v) if isinstance(v, dict) else v
                for k, v in data["dependencies"].items()
            },
            instance_params=data.get("instance_params"),
        )


@dataclass
class ComponentInstance:
    name: str
    version: str
    config: ComponentInstanceConfig | dict
    input_schema: dict | None = None
    output_schema: dict | None = None

    def __post_init__(self):
        if not isinstance(self.name, str) or self.name == "":
            raise ValueError("name must be provided")
        if not isinstance(self.version, str) or self.version == "":
            raise ValueError("version must be provided")

        if not isinstance(self.config, (ComponentInstanceConfig, dict)):
            raise ValueError("config must be `ComponentInstanceConfig` or dict")
        if isinstance(self.config, dict):
            self.config = ComponentInstanceConfig.from_dict(self.config)

    @classmethod
    def from_dict(cls, data: dict) -> "ComponentInstance":
        return cls(
            name=data["name"],
            version=data["version"],
            config=ComponentInstanceConfig.from_dict(data["config"]),
            input_schema=data.get("input_schema"),
            output_schema=data.get("output_schema"),
        )

    def alias(self) -> str:
        return component_version_alias(self.name, self.version)


class ComponentGraph(Node, Graph):
    def __init__(
        self,
        name: str,
        description: str,
        nodes: list[Node],
        input_schema: dict[str, type],
        dependencies: dict[str, Any],
        reference: str | None = None,
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

        self.reference = reference
        self.output_node = _find_output_node(nodes)

    @classmethod
    def from_spec(
        cls, definition: ComponentDefinition, instance: ComponentInstance
    ) -> "ComponentGraph":
        instance_params = instance.config.instance_params
        resolved_nodes = [
            _apply_instance_params(
                n, definition.instance_params_schema, instance_params
            )
            for n in definition.nodes
        ]

        return cls(
            name=instance.config.name,
            reference=instance.alias(),
            description=instance.config.description,
            nodes=resolved_nodes,
            input_schema=definition.input_schema,
            dependencies=instance.config.dependencies,
        )

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


def check_all_parameters_specified(
    definition: ComponentDefinition,
    instance: ComponentInstance,
):
    if len(definition.instance_params_schema) == 0:
        return

    params = instance.config.instance_params
    if params is None:
        msg = f"[{instance.name}]: Instance params not specified"
        raise ValueError(msg)

    for name, typ in definition.instance_params_schema.items():
        value = params.get(name)
        if value is None:
            msg = f"[{instance.name}]: No value for param '{name}' of type '{typ}'"
            raise ValueError(msg)
        if not isinstance(value, typ):
            msg = f"[{instance.name}]: type mismatch for param '{name}', expected '{typ}', got '{type(value)}'"
            raise TypeError(msg)


# Check on Node if it has InstanceParam parameters
# => If it does, update the value with the value defined in the component instance.
# 1. All params that are InstanceParams are in the schema
# 2. Attribute values
def _apply_instance_params(
    _node: Node,
    schema: dict[str, type],
    params: dict[str, Any],
) -> Node:
    # We create a copy to avoid modifying the original while scanning it
    node = deepcopy(_node)
    node_vars = vars(_node)
    for param_name, obj in node_vars.items():
        if isinstance(obj, InstanceParam):
            # TODO: check this when creating the component
            desired_type = schema.get(obj.name)
            if desired_type is None:
                raise ValueError(
                    f"Param {obj.name} in node {node.name} was not specified in the schema"
                )

            # This assumes we've checked that all entries in the schema
            # are specified and match the desired type.
            value = params[obj.name]
            setattr(node, param_name, value)

    return node


def component_version_alias(name: str, version: str):
    return f"{name}:{version}"


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

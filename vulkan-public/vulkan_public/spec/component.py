from dataclasses import dataclass, field
from typing import Any

from vulkan_public.spec.dependency import Dependency
from vulkan_public.spec.graph import GraphDefinition
from vulkan_public.spec.nodes import Node, NodeType


@dataclass
class InstanceParam:
    name: str


@dataclass
class ComponentDefinition(GraphDefinition):
    """A component definition specifies the workflow of a component.

    It provides an abstraction to define reusable blocks of code that can be
    instanced in multiple policies.

    Parameters
    ----------
    nodes : list[Node]
        The nodes that compose the component.
        Each node represents a step in the workflow, and can be thought of as
        a function that executes in an isolated environment.
    input_schema : dict[str, type]
        The schema for the input of the component.
        It is a dictionary where the key is the name of the input parameter, and
        the value is the type of the parameter.
    instance_params_schema : dict[str, type], optional
        The schema for the instance parameters the component.
        Similar to the input schema. It is used to specify the parameters
        that can be passed to the component when it is instanced.
    config_variables : list[str], optional
        The configuration variables that are used to parameterize the component.
        They provide a way to customize the behavior of the component without
        changing the underlying logic.

    """

    nodes: list[Node]
    input_schema: dict[str, type]
    instance_params_schema: dict[str, type] = field(default_factory=dict)
    config_variables: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.validate_nodes()
        nodes = {node.name: node.dependencies for node in self.nodes}
        self.validate_node_dependencies(nodes)
    
    def validate_nodes(self):
        terminate_nodes = [
            node for node in self.nodes if node.type == NodeType.TERMINATE
        ]
        if len(terminate_nodes) > 0:
            raise ValueError("A Component cannot have Terminate nodes")


@dataclass
class ComponentInstanceConfig:
    name: str
    description: str
    dependencies: dict[str, Dependency]
    instance_params: dict[str, Any] = field(default_factory=dict)

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
        )

    def alias(self) -> str:
        return component_version_alias(self.name, self.version)


def component_version_alias(name: str, version: str):
    return f"{name}_{version}"

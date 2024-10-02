from dataclasses import dataclass, field
from typing import Any

from vulkan_public.spec.dependency import Dependency
from vulkan_public.spec.graph import GraphDefinition
from vulkan_public.spec.nodes import Node


@dataclass
class InstanceParam:
    name: str


@dataclass
class ComponentDefinition(GraphDefinition):
    nodes: list[Node]
    input_schema: dict[str, type]
    instance_params_schema: dict[str, type] = field(default_factory=dict)

    def __post_init__(self):
        nodes = {node.name: node.dependencies for node in self.nodes}
        self.validate_node_dependencies(nodes)


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


def component_version_alias(name: str, version: str):
    return f"{name}:{version}"

from dataclasses import dataclass
from enum import Enum


class PackagingMode(Enum):
    PYTHON_MODULE = "python_module"
    PYTHON_PACKAGE = "python_package"


@dataclass
class PackagingConfig:
    mode: PackagingMode
    entrypoint: str | None

    def __post_init__(self):
        if self.mode == PackagingMode.PYTHON_PACKAGE and self.entrypoint is None:
            raise ValueError("entrypoint must be provided for python_module packaging")


@dataclass
class ComponentVersionInfo:
    name: str
    version: str
    input_schema: dict | None
    output_schema: dict | None

    def __post_init__(self):
        if not isinstance(self.name, str) or self.name == "":
            raise ValueError("name must be provided")
        if not isinstance(self.version, str) or self.version == "":
            raise ValueError("version must be provided")

    @classmethod
    def from_dict(cls, data: dict) -> "ComponentVersionInfo":
        return cls(
            name=data["name"],
            version=data["version"],
            input_schema=data.get("input_schema"),
            output_schema=data.get("output_schema"),
        )

    def alias(self) -> str:
        return f"{self.name}:{self.version}"


@dataclass
class VulkanWorkspaceConfig:
    name: str
    packaging: PackagingConfig
    components: dict[str, ComponentVersionInfo] | None

    @classmethod
    def from_dict(cls, data: dict) -> "VulkanWorkspaceConfig":
        components = [
            ComponentVersionInfo.from_dict(c) for c in data.get("components", [])
        ]
        return cls(
            name=data["name"],
            packaging=PackagingConfig(
                mode=PackagingMode(data["packaging"]["mode"]),
                entrypoint=data["packaging"].get("entrypoint"),
            ),
            components=components,
        )

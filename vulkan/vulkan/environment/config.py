from dataclasses import dataclass
from enum import Enum

from vulkan.core.component import ComponentInstance


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
class VulkanWorkspaceConfig:
    name: str
    packaging: PackagingConfig
    components: dict[str, ComponentInstance] | None

    @classmethod
    def from_dict(cls, data: dict) -> "VulkanWorkspaceConfig":
        components = [
            ComponentInstance.from_dict(c) for c in data.get("components", [])
        ]
        return cls(
            name=data["name"],
            packaging=PackagingConfig(
                mode=PackagingMode(data["packaging"]["mode"]),
                entrypoint=data["packaging"].get("entrypoint"),
            ),
            components=components,
        )

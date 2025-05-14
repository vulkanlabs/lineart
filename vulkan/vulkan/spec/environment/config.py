from dataclasses import dataclass
from enum import Enum

VULKAN_CONFIG_FILENAME = "vulkan.yaml"


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
class UserWorkspaceConfig:
    packaging: PackagingConfig

    @classmethod
    def from_dict(cls, data: dict) -> "UserWorkspaceConfig":
        return cls(
            packaging=PackagingConfig(
                mode=PackagingMode(data["packaging"]["mode"]),
                entrypoint=data["packaging"].get("entrypoint"),
            ),
        )

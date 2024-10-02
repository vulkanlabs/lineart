import os
from dataclasses import dataclass
from enum import Enum

import yaml

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
class VulkanWorkspaceConfig:
    packaging: PackagingConfig

    @classmethod
    def from_dict(cls, data: dict) -> "VulkanWorkspaceConfig":
        return cls(
            packaging=PackagingConfig(
                mode=PackagingMode(data["packaging"]["mode"]),
                entrypoint=data["packaging"].get("entrypoint"),
            ),
        )

    @classmethod
    def from_workspace(cls, workspace_path: str) -> "VulkanWorkspaceConfig":
        file_path = os.path.join(workspace_path, VULKAN_CONFIG_FILENAME)
        with open(file_path, "r") as fn:
            config_data = yaml.safe_load(fn)
        return cls.from_dict(config_data)


def get_working_directory(
    config: VulkanWorkspaceConfig,
    workspace_path: str,
) -> tuple[str, str]:
    if config.packaging.mode == PackagingMode.PYTHON_PACKAGE:
        working_directory = workspace_path
        module_name = config.packaging.entrypoint
    else:
        raise ValueError(f"Unsupported packaging mode: {config.packaging.mode}")

    return working_directory, module_name

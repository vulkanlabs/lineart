import os
from dataclasses import dataclass

import yaml

from vulkan.spec.environment.config import (
    VULKAN_CONFIG_FILENAME,
    PackagingMode,
    UserWorkspaceConfig,
)
from vulkan.spec.environment.packing import find_package_entrypoint


@dataclass
class VulkanCodeLocation:
    working_dir: str
    module_name: str
    entrypoint: str

    @classmethod
    def from_workspace(cls, workspace_path: str) -> "VulkanCodeLocation":
        file_path = os.path.join(workspace_path, VULKAN_CONFIG_FILENAME)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with open(file_path, "r") as fn:
            config_data = yaml.safe_load(fn)

        user_config = UserWorkspaceConfig.from_dict(config_data)
        working_dir, module_name = _get_working_directory(user_config, workspace_path)
        code_path = os.path.join(working_dir, module_name)
        entrypoint = find_package_entrypoint(code_path)

        return cls(
            working_dir=working_dir,
            module_name=module_name,
            entrypoint=entrypoint,
        )


def _get_working_directory(
    config: UserWorkspaceConfig,
    workspace_path: str,
) -> tuple[str, str]:
    if config.packaging.mode == PackagingMode.PYTHON_PACKAGE:
        working_directory = workspace_path
        module_name = config.packaging.entrypoint
    else:
        raise ValueError(f"Unsupported packaging mode: {config.packaging.mode}")

    return working_directory, module_name

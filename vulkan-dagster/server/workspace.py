import os
from dataclasses import dataclass

from vulkan_public.spec.environment.config import (
    VulkanWorkspaceConfig,
    get_working_directory,
)
from vulkan_public.spec.environment.packing import (
    find_package_entrypoint,
)


@dataclass
class VulkanCodeLocation:
    working_dir: str
    module_name: str
    entrypoint: str


def get_code_location(workspace_path: str):
    config = VulkanWorkspaceConfig.from_workspace(workspace_path)
    working_dir, module_name = get_working_directory(config, workspace_path)
    code_path = os.path.join(working_dir, module_name)
    entrypoint = find_package_entrypoint(code_path)
    return VulkanCodeLocation(
        working_dir=working_dir,
        module_name=module_name,
        entrypoint=entrypoint,
    )

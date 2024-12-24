import logging

from vulkan.core.context import VulkanExecutionContext


class BeamLogManager(logging.Logger):
    def __init__(self, level: int = logging.DEBUG) -> None:
        super().__init__("vulkan", level=level)


def make_beam_context(env: dict | None = None) -> VulkanExecutionContext:
    return VulkanExecutionContext(logger=BeamLogManager(), env=env)

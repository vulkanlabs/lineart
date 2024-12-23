from vulkan.core.context import VulkanExecutionContext


class DummyLogger:
    def debug(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def critical(self, *args, **kwargs):
        pass


def make_beam_context(env: dict | None = None) -> VulkanExecutionContext:
    return VulkanExecutionContext(logger=DummyLogger, env=env)

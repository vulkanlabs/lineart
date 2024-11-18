from vulkan_public.spec.context import ExecutionContext


class VulkanExecutionContext(ExecutionContext):
    def __init__(self, logger, env):
        self._logger = logger
        self._env = env

    @property
    def log(self):
        return self._logger

    @property
    def env(self):
        return self._env

import logging

from vulkan.spec.context import ExecutionContext


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

    def __getstate__(self):
        d = self.__dict__.copy()
        d["_logger_name"] = self._logger.name
        del d["_logger"]
        return d

    def __setstate__(self, d: dict):
        if "_logger_name" in d:
            d["_logger"] = logging.getLogger(d["_logger_name"])
            del d["_logger_name"]

        self.__dict__.update(d)

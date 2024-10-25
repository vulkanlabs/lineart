from logging import Logger

from fastapi import HTTPException


class ExceptionHandler:
    def __init__(self, logger: Logger, base_msg: str):
        self.logger = logger
        self.base_msg = base_msg

    def raise_exception(
        self,
        status_code: int,
        error: str,
        msg: str,
        metadata: dict | None = None,
    ):
        msg = f"{self.base_msg}: {msg}"
        self.logger.error(msg)
        detail = dict(error=error, msg=msg, metadata=metadata)
        raise HTTPException(status_code=status_code, detail=detail)


class VulkanServerException(Exception):
    def __init__(self, msg: str, status_code: int, error_code: str):
        self.msg = msg
        self.status_code = status_code
        self.error_code = error_code


# 4xx
class InvalidInputDataException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 400, "INVALID_INPUT_DATA")


class VariablesNotSetException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 400, "VARIABLES_NOT_SET")


class NotFoundException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 404, "NOT_FOUND")


class ComponentNotFoundException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 404, "COMPONENT_NOT_FOUND")


class DataSourceNotFoundException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 404, "DATA_SOURCE_NOT_FOUND")


# 5xx
class UnhandledException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 500, "UNHANDLED_EXCEPTION")

from logging import Logger

from fastapi import HTTPException, Response
from requests import JSONDecodeError
from vulkan_public.exceptions import UNHANDLED_ERROR_NAME, VULKAN_INTERNAL_EXCEPTIONS


def raise_interservice_error(logger: Logger, response: Response, message: str) -> None:
    try:
        detail = response.json()["detail"]
        if not isinstance(detail, dict):
            logger.error(f"Got err: {detail}")
            error_msg = f"{message}: {detail}"
            raise ValueError(error_msg)

        error_msg = f"{message}: {detail}"
        if detail["error"] == "VulkanInternalException":
            logger.error(f"Got err: {detail}")
            exception = VULKAN_INTERNAL_EXCEPTIONS[detail["exit_status"]]
            raise exception(msg=detail["msg"])

    except (JSONDecodeError, KeyError):
        error_msg = f"{message}: {UNHANDLED_ERROR_NAME}"

    raise ValueError(error_msg)


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

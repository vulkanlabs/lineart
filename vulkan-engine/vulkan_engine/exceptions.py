from logging import Logger

from requests import JSONDecodeError, Response
from vulkan.exceptions import UNHANDLED_ERROR_NAME, VULKAN_INTERNAL_EXCEPTIONS


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


class DataObjectNotFoundException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 404, "DATA_OBJECT_NOT_FOUND")


# 5xx
class UnhandledException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 500, "UNHANDLED_EXCEPTION")


class RunPollingTimeoutException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 504, "RUN_POLLING_TIMEOUT")


# Business Logic Exceptions
class PolicyNotFoundException(NotFoundException):
    def __init__(self, msg: str):
        super().__init__(msg)
        self.error_code = "POLICY_NOT_FOUND"


class PolicyVersionNotFoundException(NotFoundException):
    def __init__(self, msg: str):
        super().__init__(msg)
        self.error_code = "POLICY_VERSION_NOT_FOUND"


class PolicyHasVersionsException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 400, "POLICY_HAS_VERSIONS")


class InvalidPolicyVersionException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 400, "INVALID_POLICY_VERSION")


class PolicyVersionInUseException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 400, "POLICY_VERSION_IN_USE")


class InvalidAllocationStrategyException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 400, "INVALID_ALLOCATION_STRATEGY")


class RunNotFoundException(NotFoundException):
    def __init__(self, msg: str):
        super().__init__(msg)
        self.error_code = "RUN_NOT_FOUND"


class DataSourceAlreadyExistsException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 409, "DATA_SOURCE_ALREADY_EXISTS")


class InvalidDataSourceException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 400, "INVALID_DATA_SOURCE")


class WorkflowNotFoundException(NotFoundException):
    def __init__(self, msg: str):
        super().__init__(msg)
        self.error_code = "WORKFLOW_NOT_FOUND"


# Data Broker Exceptions
class DataBrokerRequestException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 502, "DATA_BROKER_REQUEST_ERROR")


class DataBrokerException(VulkanServerException):
    def __init__(self, msg: str):
        super().__init__(msg, 500, "DATA_BROKER_ERROR")

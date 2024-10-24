class UserCodeException(Exception):
    def __init__(self, node_name: str):
        self.node_name = node_name
        super().__init__(f"User code in node {node_name} raised an exception")


class UserImportException(Exception):
    def __init__(self, msg: str):
        super().__init__(f"Import-related issue from user code: {msg}")


class VulkanInternalException(Exception):
    def __init__(
        self, exit_status: int, msg: str | None = None, metadata: dict | None = None
    ):
        self.exit_status = exit_status
        self.metadata = metadata
        super().__init__(msg)


class DefinitionNotFoundException(VulkanInternalException):
    def __init__(self, msg: str | None = None, metadata: dict | None = None):
        super().__init__(exit_status=3, msg=msg, metadata=metadata)


class InvalidDefinitionError(VulkanInternalException):
    def __init__(self, msg: str | None = None, metadata: dict | None = None):
        super().__init__(exit_status=4, msg=msg, metadata=metadata)


class ConflictingDefinitionsError(VulkanInternalException):
    def __init__(self, msg: str | None = None, metadata: dict | None = None):
        super().__init__(exit_status=5, msg=msg, metadata=metadata)


class ComponentNotFoundException(VulkanInternalException):
    def __init__(self, msg: str | None = None, metadata: dict | None = None):
        super().__init__(exit_status=6, msg=msg, metadata=metadata)


class DataSourceNotFoundException(VulkanInternalException):
    def __init__(self, msg: str | None = None, metadata: dict | None = None):
        super().__init__(exit_status=7, msg=msg, metadata=metadata)


VULKAN_INTERNAL_EXCEPTIONS = {
    3: DefinitionNotFoundException,
    4: InvalidDefinitionError,
    5: ConflictingDefinitionsError,
    6: ComponentNotFoundException,
    7: DataSourceNotFoundException,
}

UNHANDLED_ERROR_NAME = "UnhandledError"

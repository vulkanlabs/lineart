import os
from logging import Logger
from shutil import rmtree

from fastapi import HTTPException

from vulkan.exceptions import UNHANDLED_ERROR_NAME, VulkanInternalException


class ExecutionContext:
    def __init__(self, logger: Logger, base_msg: str | None = None):
        self.logger = logger
        self.base_msg = base_msg
        self.exit_status = 0
        self.created_assets = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            msg = f"{self.base_msg}: {exc_val}" if self.base_msg else str(exc_val)
            self.logger.error(f"[{exc_val.__class__.__name__}] {msg}")

            if isinstance(exc_val, VulkanInternalException):
                error = exc_val.__class__.__name__
                http_status_code = HTTP_STATUS_CODES.get(error, 400)
                detail = dict(
                    error="VulkanInternalException",
                    exit_status=exc_val.exit_status,
                    msg=msg,
                    metadata=exc_val.metadata,
                )
            else:
                http_status_code = 500
                detail = dict(error=UNHANDLED_ERROR_NAME, msg=msg)

            self.cleanup()
            raise HTTPException(status_code=http_status_code, detail=detail)
        return False

    def register_asset(self, path: str):
        self.created_assets.append(path)

    def cleanup(self):
        for path in self.created_assets:
            if os.path.exists(path):
                self.logger.info(f"Removing asset: {path}")
                rmtree(path)


HTTP_STATUS_CODES = {
    "ConflictingDefinitionsError": 409,
    "DefinitionNotFoundException": 400,
    "InvalidDefinitionError": 400,
}

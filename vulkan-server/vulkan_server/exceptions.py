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

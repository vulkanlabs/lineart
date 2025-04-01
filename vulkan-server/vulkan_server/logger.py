import json
import logging
import os
import sys
from dataclasses import dataclass
from uuid import UUID

import google.cloud.logging
from fastapi import Depends
from google.cloud.logging.handlers import CloudLoggingHandler
from pydantic import BaseModel
from sqlalchemy.orm import Session

from vulkan_server.db import LogRecord, get_db

SYS_LOGGER_NAME = "vulkan"
USER_LOGGER_NAME = f"{SYS_LOGGER_NAME}.user"
GCP_LOGGER_NAME = "vulkan-server"


class EventMessage(BaseModel):
    event: str
    metadata: dict


class VulkanLogger:
    def __init__(self, db: Session):
        self.system = get_system_logger()
        self.user = get_user_logger(db)

    def event(self, event_name: str, **kwargs):
        message = EventMessage(event=event_name, metadata=kwargs)
        self.user.info(
            message.model_dump_json(),
        )


def get_logger(
    db: Session = Depends(get_db),
) -> VulkanLogger:
    return VulkanLogger(db)


def get_system_logger() -> logging.Logger:
    loggers = logging.Logger.manager.loggerDict
    if SYS_LOGGER_NAME in loggers:
        return loggers[SYS_LOGGER_NAME]
    return init_system_logger()


def get_user_logger(db: Session) -> logging.Logger:
    loggers = logging.Logger.manager.loggerDict
    if USER_LOGGER_NAME in loggers:
        return loggers[USER_LOGGER_NAME]
    return init_user_logger(db)


def init_logger(application_name: str) -> logging.Logger:
    logger = logging.getLogger(application_name)
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(sys.stdout)
    log_formatter = logging.Formatter(
        "%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s"
    )
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)
    return logger


def init_user_logger(db: Session) -> logging.Logger:
    logger = logging.getLogger(USER_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    handler = SQLAlchemyHandler(db)
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    return logger


def init_system_logger() -> logging.Logger:
    logger = logging.getLogger(SYS_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    cloud_handler = get_cloud_logging_handler()
    stream_handler = get_stream_handler()
    logger.addHandler(cloud_handler)
    logger.addHandler(stream_handler)
    return logger


def get_cloud_logging_handler():
    client = google.cloud.logging.Client(project=os.getenv("GCP_PROJECT_ID"))
    cloud_handler = CloudLoggingHandler(client, name=GCP_LOGGER_NAME, stream=sys.stdout)
    cloud_handler.setFormatter(CloudLoggingFormatter())
    return cloud_handler


def get_stream_handler():
    stream_handler = logging.StreamHandler(sys.stdout)
    log_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    stream_handler.setFormatter(log_formatter)
    return stream_handler


@dataclass
class StructuredLogRecord:
    project_id: str
    level: str
    message: str
    timestamp: str


class SQLAlchemyHandler(logging.Handler):
    def __init__(self, db):
        super().__init__()
        self.db: Session = db

    def emit(self, record):
        """
        Emit a log record and insert it into the database.
        """
        try:
            log: StructuredLogRecord = self.format(record)
            log_record = LogRecord(
                project_id=log.project_id,
                level=log.level,
                message=log.message,
                timestamp=log.timestamp,
            )
            self.db.add(log_record)
            self.db.commit()

        except Exception:
            # If something goes wrong, print to stderr (avoid infinite recursion)
            self.handleError(record)


class StructuredFormatter(logging.Formatter):
    def format(self, record):
        extra = getattr(record, "extra", {})
        return StructuredLogRecord(
            project_id=extra.get("project_id"),
            level=record.levelname,
            message=record.getMessage(),
            timestamp=self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
        )


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, type):
            return o.__name__

        if isinstance(o, UUID):
            return str(o)

        return super().default(o)


class CloudLoggingFormatter(logging.Formatter):
    def format(self, record):
        extra = getattr(record, "extra", {})
        log_record = {
            "project_id": extra.get("project_id"),
            "message": record.getMessage(),
            "extra": extra,
        }
        return json.dumps(log_record, cls=EnhancedJSONEncoder)

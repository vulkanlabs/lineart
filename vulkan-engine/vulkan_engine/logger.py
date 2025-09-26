import json
import logging
import sys
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from vulkan_engine.config import LoggingConfig
from vulkan_engine.db import LogRecord
from vulkan_engine.events import VulkanEvent
from vulkan_engine.gcp_logging import create_gcp_handler

SYS_LOGGER_NAME = "vulkan_engine"
USER_LOGGER_NAME = f"{SYS_LOGGER_NAME}.user"
GCP_LOGGER_NAME = "vulkan-server"


class EventMessage(BaseModel):
    event: VulkanEvent
    metadata: dict


class VulkanLogger(logging.Logger):
    def __init__(self, db: Session, logging_config: LoggingConfig | None = None):
        self.system = get_system_logger(logging_config)
        self.user = get_user_logger(db)
        super().__init__(name=self.system.name, level=self.system.level)

    def event(self, event_name: VulkanEvent, **kwargs):
        message = EventMessage(event=event_name, metadata=kwargs)
        self.user.info(
            message.model_dump_json(),
        )


def create_logger(
    db: Session, logging_config: LoggingConfig | None = None
) -> VulkanLogger:
    """Create VulkanLogger with configuration."""
    return VulkanLogger(db, logging_config)


def get_system_logger(logging_config: LoggingConfig | None = None) -> logging.Logger:
    """Get or initialize the system logger."""
    loggers = logging.Logger.manager.loggerDict
    if SYS_LOGGER_NAME in loggers:
        return loggers[SYS_LOGGER_NAME]
    return init_system_logger(logging_config)


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
    """Initialize user logger with SQLAlchemy handler."""
    logger = logging.getLogger(USER_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    if not any(isinstance(h, SQLAlchemyHandler) for h in logger.handlers):
        handler = SQLAlchemyHandler(db)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
    return logger


def init_system_logger(logging_config: LoggingConfig | None = None) -> logging.Logger:
    """Initialize system logger with cloud logging support."""
    logger = logging.getLogger(SYS_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        stream_handler = get_stream_handler()
        logger.addHandler(stream_handler)

    cloud_handler = get_cloud_logging_handler(logging_config)
    if cloud_handler and not any(
        isinstance(h, type(cloud_handler)) for h in logger.handlers
    ):
        logger.addHandler(cloud_handler)
    return logger


def get_cloud_logging_handler(
    logging_config: LoggingConfig | None = None,
) -> logging.Handler | None:
    if (
        logging_config
        and hasattr(logging_config, "gcp_project_id")
        and logging_config.gcp_project_id
    ):
        return create_gcp_handler(logging_config.gcp_project_id, GCP_LOGGER_NAME)
    return None


def get_stream_handler():
    stream_handler = logging.StreamHandler(sys.stdout)
    log_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    stream_handler.setFormatter(log_formatter)
    return stream_handler


@dataclass
class StructuredLogRecord:
    level: str
    message: str
    timestamp: str


class SQLAlchemyHandler(logging.Handler):
    def __init__(self, db):
        super().__init__()
        self.db: Session = db
        # Store the session maker to create independent sessions for logging
        self.session_maker = (
            db.get_bind().pool._creator if hasattr(db.get_bind(), "pool") else None
        )

    def emit(self, record):
        """
        Emit a log record and insert it into the database.
        """
        try:
            log: StructuredLogRecord = self.format(record)
            log_record = LogRecord(
                level=log.level,
                message=log.message,
                timestamp=log.timestamp,
            )

            # Use a separate session for logging to avoid transaction conflicts
            # Create a new independent session for this log entry
            if self.db.bind:
                LogSession = sessionmaker(bind=self.db.bind)
                with LogSession() as log_session:
                    log_session.add(log_record)
                    log_session.commit()
            else:
                # Fallback to original behavior if can't create separate session
                self.db.add(log_record)
                self.db.commit()

        except Exception:
            # WARNING: This exception is only logged and not propagated.
            # Consider re-raising or handling more robustly to avoid masking critical errors.
            self.handleError(record)


class StructuredFormatter(logging.Formatter):
    def format(self, record):
        return StructuredLogRecord(
            level=record.levelname,
            message=record.getMessage(),
            timestamp=self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
        )


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, BaseModel):
            return o.model_dump()
        if isinstance(o, type):
            return o.__name__

        if isinstance(o, UUID):
            return str(o)

        return super().default(o)


class CloudLoggingFormatter(logging.Formatter):
    def format(self, record):
        extra = getattr(record, "extra", {})
        log_record = {
            "message": record.getMessage(),
            "extra": extra,
        }
        return json.dumps(log_record, cls=EnhancedJSONEncoder)

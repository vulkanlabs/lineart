from enum import Enum


class RunStatus(Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class JobStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"


class WorkflowStatus(Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class DataSourceStatus(Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"

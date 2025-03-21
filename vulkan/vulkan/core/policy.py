import enum


class PolicyVersionStatus(enum.Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class WorkspaceStatus(enum.Enum):
    OK = "OK"
    CREATION_PENDING = "CREATION_PENDING"
    CREATION_FAILED = "CREATION_FAILED"

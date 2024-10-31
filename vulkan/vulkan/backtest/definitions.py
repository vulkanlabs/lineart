from enum import Enum


class BacktestStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SupportedFileFormat(Enum):
    CSV = "CSV"
    PARQUET = "PARQUET"

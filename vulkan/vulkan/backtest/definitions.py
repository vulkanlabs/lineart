from enum import Enum


class BacktestStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class SupportedFileFormat(Enum):
    CSV = "CSV"
    PARQUET = "PARQUET"

from dataclasses import dataclass

PUBLISH_IO_MANAGER_KEY = "publish_metadata_io_manager"
METADATA_OUTPUT_KEY = "metadata"


@dataclass
class StepMetadata:
    node_type: str
    start_time: float
    end_time: float
    error: str | None = None

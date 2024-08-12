from dataclasses import dataclass


@dataclass
class StepMetadata:
    node_type: str
    start_time: float
    end_time: float
    error: str | None = None
    metadata: dict[str, str] | None = None

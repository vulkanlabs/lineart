from dataclasses import dataclass
from typing import Any


@dataclass
class StepMetadata:
    node_type: str
    start_time: float
    end_time: float
    error: str | list[str] | None = None
    extra: dict[str, Any] | None = None

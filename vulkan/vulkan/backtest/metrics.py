from dataclasses import dataclass
from enum import Enum


class TargetKind(Enum):
    BINARY_DISTRIBUTION = "BINARY_DISTRIBUTION"
    BINARY_CLASSIFICATION = "BINARY_CLASSIFICATION"


@dataclass
class Target:
    name: str
    kind: TargetKind


@dataclass
class MetricsMetadata:
    outcome: str
    target: Target
    time: str | None = None
    groups: list[str] | None = None

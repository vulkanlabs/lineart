from abc import ABC, abstractmethod


class ExecutionContext(ABC):
    """Abstract class for the execution context of a Policy."""

    @property
    @abstractmethod
    def log(self):
        """The logger for the current execution."""

    @property
    @abstractmethod
    def env(self):
        """The environment dictionary for the current execution."""

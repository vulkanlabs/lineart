from abc import ABC, abstractmethod

from .nodes import Node


class ComponentGraph(ABC):
    @abstractmethod
    def nodes(self) -> list[Node]:
        pass

    @abstractmethod
    def output(self) -> str:
        pass

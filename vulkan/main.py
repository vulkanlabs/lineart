from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List
import requests


class NodeType(Enum):
    TRANSFORM = 1
    CONNECTION = 2
    BRANCH = 3


class Status(Enum):
    APPROVED = 1
    DENIED = 2


@dataclass
class Context:
    data: Dict[str, Any]
    variables: Dict[str, Any]


@dataclass
class NodeConfig:
    name: str
    description: str
    type: NodeType


@dataclass
class HTTPConnectionConfig(NodeConfig):
    url: str
    method: str
    headers: dict
    params: dict


class Node(ABC):
    
    def __init__(self, config: NodeConfig):
        self.config = config

    @abstractmethod
    def run(self, data):
        pass


class HTTPConnection(Node):

    def __init__(self, config: HTTPConnectionConfig):
        super().__init__(config)

    def run(self, data):
        response = requests.request(
            method=self.config.method,
            url=self.config.url,
            headers=self.config.headers,
            params=self.config.params,
        )
        if response.status_code == 200:
            return response.json()
        # handle exception in controller
        raise Exception("Connection failed")


class Transform(Node):

    def __init__(self, config: NodeConfig, func: Any, params: Dict[str, Any]):
        super().__init__(config)
        self.func = func
        self.params = params

    def run(self, data):
        return self.func(data)


class Branch(Node):
    
        def __init__(self, config: NodeConfig, condition: Any, params: Dict[str, Any]):
            super().__init__(config)
            self.condition = condition
            self.params = params
    
        def run(self, data):
            return self.condition(data)


class Policy:
    
    def __init__(self, context: Context):
        self.context = context

    def run(self, nodes: List[Node]):
        for node in nodes:
            if node.config.type == NodeType.CONNECTION:
                response = node.run(self.context.data)

            elif node.config.type == NodeType.BRANCH:
                response = node.run(self.context)

            elif node.config.type == NodeType.TRANSFORM:
                data = dict()
                for k, v in node.params.items():
                    data[v] = self.context.variables[k]
                response = node.run(data)

            self.context.variables.update({
                node.config.name: response
            })
        print(self.context)
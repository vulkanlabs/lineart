from dagster import asset, AssetIn
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any
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
    data: dict[str, Any]
    variables: dict[str, Any]


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
    def node(self):
        pass


class HTTPConnection(Node):

    def __init__(self, config: HTTPConnectionConfig):
        super().__init__(config)

    def node(self):
        return asset(
            self._run,
            name=self.config.name,
        )

    def _run(self):
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

    def __init__(self, config: NodeConfig, func: Any, params: dict[str, Any]):
        super().__init__(config)
        self.func = func
        self.params = params

    def node(self):
        return asset(
            self.func,
            name=self.config.name,
            ins={k: AssetIn(v) for k, v in self.params.items()},
        )
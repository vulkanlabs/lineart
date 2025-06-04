from typing import cast

from vulkan.spec.nodes.base import Node, NodeDefinition, NodeType
from vulkan.spec.nodes.metadata import ConnectionNodeMetadata


class ConnectionNode(Node):
    """A node that performs HTTP requests to external systems.

    Connection nodes are used to make HTTP requests to external APIs and services,
    allowing workflows to interact with web services and REST APIs.
    """

    def __init__(
        self,
        name: str,
        url: str,
        method: str = "GET",
        description: str | None = None,
        headers: dict | None = None,
        params: dict | None = None,
        body: dict | None = None,
        timeout: int | None = None,
        retry_max_retries: int = 1,
        response_type: str = "PLAIN_TEXT",
        dependencies: dict | None = None,
        hierarchy: list[str] | None = None,
    ):
        """Performs HTTP requests to external systems.

        Parameters
        ----------
        name : str
            The name of the node.
        url : str
            The URL to make the HTTP request to.
        method : str, optional
            The HTTP method to use (GET, POST, PUT, DELETE, etc.). Defaults to "GET".
        description : str, optional
            A description of the node.
        headers : dict, optional
            HTTP headers to include in the request.
        params : dict, optional
            Query parameters to include in the request.
        body : dict, optional
            Request body for POST/PUT requests.
        timeout : int, optional
            Request timeout in seconds.
        retry_max_retries : int, optional
            Maximum number of retry attempts. Defaults to 1.
        response_type : str, optional
            Expected response type. Defaults to "text/plain".
        dependencies : dict, optional
            The dependencies of the node.
        hierarchy : list[str], optional
            The hierarchy of the node.
        """
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.CONNECTION,
            dependencies=dependencies,
            hierarchy=hierarchy,
        )
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.params = params or {}
        self.body = body or {}
        self.timeout = timeout
        self.retry_max_retries = retry_max_retries
        self.response_type = response_type

    def node_definition(self) -> NodeDefinition:
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.dependencies,
            metadata=ConnectionNodeMetadata(
                url=self.url,
                method=self.method,
                headers=self.headers,
                params=self.params,
                body=self.body,
                timeout=self.timeout,
                retry_max_retries=self.retry_max_retries,
                response_type=self.response_type,
            ),
            hierarchy=self.hierarchy,
        )

    @classmethod
    def from_dict(cls, spec: dict) -> "ConnectionNode":
        definition = NodeDefinition.from_dict(spec)
        if definition.metadata is None:
            raise ValueError(f"Metadata not set for node {definition.name}")

        metadata = cast(ConnectionNodeMetadata, definition.metadata)
        return cls(
            name=definition.name,
            description=definition.description,
            dependencies=definition.dependencies,
            url=metadata.url,
            method=metadata.method,
            headers=metadata.headers,
            params=metadata.params,
            body=metadata.body,
            timeout=metadata.timeout,
            retry_max_retries=metadata.retry_max_retries,
            response_type=metadata.response_type,
            hierarchy=definition.hierarchy,
        )

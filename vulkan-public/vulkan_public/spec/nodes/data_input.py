from vulkan_public.spec.nodes.base import Node, NodeDefinition, NodeType


class DataInputNode(Node):
    """A node that represents an input data source.

    Data input nodes are used to fetch data from external systems and pass
    it to the rest of the workflow.
    """

    def __init__(
        self,
        name: str,
        source: str,
        description: str | None = None,
        dependencies: dict | None = None,
    ):
        """Fetches data from a pre-configured data source.

        Parameters
        ----------
        name : str
            The name of the node.
        source: str
            The name of the configured data source.
        description: str, optional
            A description of the node. Used for documentation purposes and
            shown in the user interface.
        dependencies: dict, optional
            The dependencies of the node.
            See `Dependency` for more information.

        """
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.DATA_INPUT,
            dependencies=dependencies,
        )
        self.source = source

    def node_definition(self) -> NodeDefinition:
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.dependencies,
            metadata={
                "data_source": self.source,
            },
        )

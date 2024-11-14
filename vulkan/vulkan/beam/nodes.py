from abc import ABC
from functools import partial

import apache_beam as beam
from vulkan_public.spec.dependency import Dependency
from vulkan_public.spec.nodes import (
    BranchNode,
    DataInputNode,
    InputNode,
    Node,
    TerminateNode,
    TransformNode,
)


class BeamNode(ABC):
    """Base class for all Beam nodes"""

    pass


class BeamInput(InputNode, BeamNode):
    def __init__(
        self,
        name: str,
        source: str,
        schema: dict[str, type],
        description: str | None = None,
    ):
        super().__init__(name=name, description=description, schema=schema)
        self.source = source

    @classmethod
    def from_spec(cls, node: InputNode, source: str):
        return cls(
            name=node.name,
            description=node.description,
            source=source,
            schema=node.schema,
        )


class BeamDataInput(DataInputNode, BeamNode):
    def __init__(
        self,
        name: str,
        source: str,
        description: str | None = None,
        dependencies: dict | None = None,
    ):
        super().__init__(
            name=name,
            source=source,
            description=description,
            dependencies=dependencies,
        )

    @classmethod
    def from_spec(cls, node: DataInputNode):
        return cls(
            name=node.name,
            source=node.source,
            description=node.description,
            dependencies=node.dependencies,
        )


class BeamTransformFn(beam.DoFn):
    def __init__(self, func: callable, dependencies: dict[str, Dependency]):
        self.func = func
        self.dependencies = dependencies

    def process(self, element, **kwargs):
        key, value = element
        inputs = self.__make_inputs(value)
        yield (key, self.func(**inputs))

    def __make_inputs(self, value):
        if len(self.dependencies) > 1:
            return {
                name: value[str(dependency)][0]
                for name, dependency in self.dependencies.items()
            }
        name = list(self.dependencies.keys())[0]
        return {name: value}


class BeamLogicNode(BeamNode):
    """Base class for nodes that execute a user-defined function"""

    def op(self) -> beam.ParDo:
        return beam.ParDo(BeamTransformFn(self.func, self.dependencies))

    def with_context(self, context: dict) -> "BeamLogicNode":
        if self.func.__code__.co_varnames[0] == "context":
            self.func = partial(self.func, context=context)
        return self


class BeamTransform(TransformNode, BeamLogicNode):
    def __init__(
        self,
        name: str,
        func: callable,
        dependencies: dict[str, Dependency],
        description: str | None = None,
        hidden: bool = False,
    ):
        super().__init__(
            name=name,
            description=description,
            func=func,
            dependencies=dependencies,
            hidden=hidden,
        )

    @classmethod
    def from_spec(cls, node: TransformNode):
        return cls(
            name=node.name,
            description=node.description,
            func=node.func,
            dependencies=node.dependencies,
            hidden=node.hidden,
        )


class BeamBranch(BranchNode, BeamLogicNode):
    def __init__(
        self,
        name: str,
        func: callable,
        outputs: list[str],
        dependencies: dict[str, Dependency],
        description: str | None = None,
    ):
        super().__init__(
            name=name,
            description=description,
            func=func,
            outputs=outputs,
            dependencies=dependencies,
        )

    @classmethod
    def from_spec(cls, node: BranchNode):
        return cls(
            name=node.name,
            description=node.description,
            func=node.func,
            outputs=node.outputs,
            dependencies=node.dependencies,
        )


class BeamTerminateFn(beam.DoFn):
    def __init__(self, return_status: str):
        self.return_status = return_status

    def process(self, element, **kwargs):
        yield (element[0], {"status": self.return_status})


class BeamTerminate(TerminateNode, BeamNode):
    def __init__(
        self,
        name: str,
        return_status: str,
        dependencies: dict[str, Dependency],
        description: str | None = None,
    ):
        super().__init__(
            name=name,
            description=description,
            return_status=return_status,
            dependencies=dependencies,
            callback=None,
        )

    @classmethod
    def from_spec(cls, node: TerminateNode):
        return cls(
            name=node.name,
            description=node.description,
            return_status=node.return_status,
            dependencies=node.dependencies,
        )

    def op(self):
        return beam.ParDo(BeamTerminateFn(self.return_status))


_NODE_TYPE_MAP: dict[type[Node], type[BeamNode]] = {
    DataInputNode: BeamDataInput,
    TransformNode: BeamTransform,
    BranchNode: BeamBranch,
    TerminateNode: BeamTerminate,
}


def to_beam_nodes(nodes: list[Node]) -> list[BeamNode]:
    return [to_beam_node(node) for node in nodes]


def to_beam_node(node: Node) -> BeamNode:
    typ = type(node)
    impl_type = _NODE_TYPE_MAP.get(typ)
    if impl_type is None:
        msg = f"Node type {typ} has no known Beam implementation"
        raise ValueError(msg)

    return impl_type.from_spec(node)

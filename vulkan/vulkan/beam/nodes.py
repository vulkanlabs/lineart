from abc import ABC

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

    def read(self):
        # read input according to config (e.g. from file, database, etc.)
        pass


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

    def read(self):
        return beam.io.ReadFromText(self.source)


class BeamTransformFn(beam.DoFn):
    def __init__(self, func: callable, dependencies: dict[str, Dependency]):
        self.func = func
        self.dependencies = dependencies

    def process(self, element, **kwargs):
        key, value = element
        inputs = self._make_inputs(value)
        yield (key, self.func(**inputs, **kwargs))

    def _make_inputs(self, value):
        if len(self.dependencies) > 1:
            return {name: value[str(dep)][0] for name, dep in self.dependencies.items()}
        name = list(self.dependencies.keys())[0]
        return {name: value}


class BeamTransform(TransformNode, BeamNode):
    def __init__(
        self,
        name: str,
        func: callable,
        dependencies: dict[str, Dependency],
        description: str | None = None,
        hidden: bool = False,
        env: dict | None = None,
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

    def op(self):
        return beam.ParDo(BeamTransformFn(self.func, self.dependencies))

    def with_env(self, env: dict) -> "BeamTransform":
        self.env = env
        return self


class BeamBranch(BranchNode, BeamNode):
    def __init__(
        self,
        name: str,
        func: callable,
        outputs: list[str],
        dependencies: dict[str, Dependency],
        description: str | None = None,
        env: dict | None = None,
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

    def op(self):
        return beam.ParDo(BeamTransformFn(self.func, self.dependencies))

    def with_env(self, env: dict) -> "BeamBranch":
        self.env = env
        return self


class BeamTerminateFn(beam.DoFn):
    def __init__(self, return_status: str):
        self.return_status = return_status

    def process(self, element, **kwargs):
        yield (element[0], {"status": self.return_status})
        # yield {"key": element[0], "status": self.return_status}


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

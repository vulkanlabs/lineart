from abc import ABC
from functools import partial
from json import JSONDecodeError
from typing import Callable

import apache_beam as beam
from apache_beam.pvalue import TaggedOutput
from apache_beam.transforms.enrichment import Enrichment, EnrichmentSourceHandler
from pyarrow import parquet as pq

from vulkan.connections import HTTPConfig
from vulkan.core.context import VulkanExecutionContext
from vulkan.http_client import HTTPClient
from vulkan.schemas import (
    DataSourceSpec,
    HTTPSource,
    LocalFileSource,
    RegisteredFileSource,
)
from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes import (
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
        data_path: str,
        schema: dict[str, type],
        description: str | None = None,
        hierarchy: list[str] | None = None,
    ):
        super().__init__(
            name=name,
            description=description,
            schema=schema,
            hierarchy=hierarchy,
        )
        self.data_path = data_path

    @classmethod
    def from_spec(cls, node: InputNode, data_path: str):
        return cls(
            name=node.name,
            description=node.description,
            data_path=data_path,
            schema=node.schema,
            hierarchy=node._hierarchy,
        )


# TODO: this handler needs the data source keys to retrieve
# specific rows from the request.
class _FileHandler(EnrichmentSourceHandler):
    def __init__(
        self, context: VulkanExecutionContext, source: str, path: str, keys: str
    ):
        self.context = context
        self.source = source
        self.path = path
        self.keys = keys
        self._df = None

    def __enter__(self):
        # TODO: This is loading the entire dataset to memory.
        # maybe rewrite with pyarrow table instead
        dataset = pq.ParquetDataset(self.path)
        self._df = dataset.read().to_pandas()
        diff = set(self.keys) - set(self._df.columns)
        if len(diff) > 0:
            raise ValueError(f"Keys {diff} not found in file {self.path}")
        self.context.log.debug(f"Loaded {len(self._df)} rows from {self.path}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._df = None

    def __call__(self, request: tuple, *args, **kwargs):
        key = request[0]
        values = request[1]

        # Match rows based on lookup keys
        #    SELECT *
        #      FROM self._df
        #     WHERE colA = @values.colA
        #           ...
        query_str = " & ".join([f'{k} == @values["{k}"]' for k in self.keys])
        matching_rows = self._df.query(query_str)

        if len(matching_rows) == 0:
            response_data = None
        else:
            response_data = matching_rows.iloc[0].to_dict()

        req = beam.Row(key=key, **values)
        response = beam.Row(
            op_data=response_data,
            op_metadata={"source": self.source, "rows_matched": len(matching_rows)},
        )

        return req, response


class _HTTPHandler(EnrichmentSourceHandler):
    def __init__(
        self, context: VulkanExecutionContext, source: str, spec: DataSourceSpec
    ):
        self.context = context
        self.source = source
        self.spec = spec

    def __enter__(self):
        pass

    def __call__(self, request: tuple, *args, **kwargs):
        key = request[0]
        values = request[1]

        config = HTTPConfig(
            url=self.spec.source.url,
            method=self.spec.source.method,
            headers=self.spec.source.headers or {},
            params=self.spec.source.params or {},
            body=self.spec.source.body or {},
            timeout=self.spec.source.timeout,
            retry=self.spec.source.retry,
            response_type=self.spec.source.response_type,
        )
        client = HTTPClient(config)
        raw_response = client.execute_raw(values, self.context.env)

        response_data = None
        if raw_response.status_code == 200:
            try:
                response_data = raw_response.json()
            except JSONDecodeError:
                response_data = raw_response.content

        req = beam.Row(key=key, **values)
        response = beam.Row(
            op_data=response_data,
            op_metadata={
                "source": self.source,
                "status_code": raw_response.status_code,
                "headers": dict(raw_response.headers),
            },
        )

        return req, response


class BeamDataInput(DataInputNode, BeamNode):
    def __init__(
        self,
        name: str,
        spec: DataSourceSpec,
        description: str | None = None,
        dependencies: dict | None = None,
        hierarchy: list[str] | None = None,
    ):
        super().__init__(
            name=name,
            data_source=spec.name,
            description=description,
            dependencies=dependencies,
            hierarchy=hierarchy,
        )
        self.spec = spec

    @classmethod
    def from_spec(cls, node: DataInputNode, spec: DataSourceSpec):
        return cls(
            name=node.name,
            spec=spec,
            description=node.description,
            dependencies=node.dependencies,
            hierarchy=node._hierarchy,
        )

    def op(self) -> beam.PTransform:
        enrich = Enrichment(source_handler=self._handler())
        split = enrich | f"{self.name} - Extract Data and Metadata" >> beam.ParDo(
            _ExtractDataAndMetadataFn()
        ).with_outputs("metadata", main="data")
        return split

    def _handler(self) -> EnrichmentSourceHandler:
        if isinstance(self.spec.source, HTTPSource):
            return _HTTPHandler(
                self.context,
                self.data_source,
                self.spec,
            )
        elif isinstance(self.spec.source, (LocalFileSource, RegisteredFileSource)):
            return _FileHandler(
                self.context,
                self.data_source,
                self.spec.source.path,
            )
        else:
            raise NotImplementedError(
                f"Source type {type(self.spec.source)} not supported"
            )

    def with_context(self, context: VulkanExecutionContext) -> "BeamDataInput":
        self.context = context
        return self


class _ExtractDataAndMetadataFn(beam.DoFn):
    def process(self, element: beam.Row, *args, **kwargs):
        key = element.key
        yield (key, element.op_data)
        yield TaggedOutput("metadata", (key, element.op_metadata))


class BeamTransformFn(beam.DoFn):
    def __init__(self, func: callable, dependencies: dict[str, Dependency]):
        self.func = func
        self.dependencies = dependencies

    def process(self, element, **kwargs):
        key, value = element
        inputs = self.__make_inputs(value)
        yield (key, self.func(**inputs))

    def __make_inputs(self, value):
        deps = {}
        for name, dependency in self.dependencies.items():
            dep = value[str(dependency)]
            if len(dep) == 0:
                # Skip empty dependencies: those are usually control signals
                # emitted by Branch nodes.
                deps[name] = None
            else:
                deps[name] = dep[0]
        return deps


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
        hierarchy: list[str] | None = None,
    ):
        super().__init__(
            name=name,
            description=description,
            func=func,
            dependencies=dependencies,
            hierarchy=hierarchy,
        )

    @classmethod
    def from_spec(cls, node: TransformNode):
        return cls(
            name=node.name,
            description=node.description,
            func=node.func,
            dependencies=node.dependencies,
            hierarchy=node._hierarchy,
        )


class BeamBranch(BranchNode, BeamLogicNode):
    def __init__(
        self,
        name: str,
        func: Callable,
        choices: list[str],
        dependencies: dict[str, Dependency],
        description: str | None = None,
        hierarchy: list[str] | None = None,
    ):
        super().__init__(
            name=name,
            func=func,
            choices=choices,
            dependencies=dependencies,
            description=description,
            hierarchy=hierarchy,
        )

    @classmethod
    def from_spec(cls, node: BranchNode):
        return cls(
            name=node.name,
            func=node.func,
            choices=node.choices,
            dependencies=node.dependencies,
            description=node.description,
            hierarchy=node._hierarchy,
        )


class BeamTerminateFn(beam.DoFn):
    def __init__(self, return_status: str, return_metadata: dict[str, Dependency]):
        self.return_status = return_status
        self.return_metadata = return_metadata

    def process(self, element, **kwargs):
        metadata = None
        if self.return_metadata is not None:
            metadata = {}
            for name, dep in self.return_metadata.items():
                metadata[name] = element[1][str(dep)]

        yield (element[0], {"status": self.return_status, "metadata": metadata})


class BeamTerminate(TerminateNode, BeamNode):
    def __init__(
        self,
        name: str,
        return_status: str,
        dependencies: dict[str, Dependency],
        output_data: dict[str, str] | None = None,
        description: str | None = None,
        hierarchy: list[str] | None = None,
    ):
        super().__init__(
            name=name,
            description=description,
            return_status=return_status,
            dependencies=dependencies,
            output_data=output_data,
            callback=None,
            hierarchy=hierarchy,
        )

    @classmethod
    def from_spec(cls, node: TerminateNode):
        return cls(
            name=node.name,
            description=node.description,
            return_status=node.return_status,
            dependencies=node.dependencies,
            output_data=node.output_data,
            hierarchy=node._hierarchy,
        )

    def op(self):
        return beam.ParDo(BeamTerminateFn(self.return_status, self.return_metadata))


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
    if typ == InputNode:
        return _identity_transform(node)

    impl_type = _NODE_TYPE_MAP.get(typ)
    if impl_type is None:
        msg = f"Node type {typ} has no known Beam implementation"
        raise ValueError(msg)

    return impl_type.from_spec(node)


def _identity_transform(node: BeamNode) -> BeamTransform:
    return BeamTransform(
        name=node.name,
        func=_identity,
        dependencies=node.dependencies,
        description=node.description,
        hierarchy=node._hierarchy,
    )


def _identity(**kwargs):
    if len(kwargs) == 1:
        return list(kwargs.values())[0]
    return kwargs

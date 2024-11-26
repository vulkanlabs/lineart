import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from vulkan_public.spec.dependency import INPUT_NODE, Dependency

from vulkan.beam.io import (
    ProcessResultFn,
    ReadParquet,
    ReadRemoteCSV,
    to_pyarrow_schema,
)
from vulkan.beam.nodes import (
    BeamBranch,
    BeamInput,
    BeamTerminate,
)
from vulkan.beam.pipeline import build_pipeline


def test_read_from_gcs():
    input_node = BeamInput(
        name=INPUT_NODE,
        schema={"tax_id": str, "score": int},
        source="gs://vulkan-dev-beam-temp/input_data.csv",
    )

    def _branch(data):
        print(data)
        if data["score"] > 500:
            return "approved"
        return "denied"

    branch = BeamBranch(
        name="branch",
        func=_branch,
        outputs=["approved", "denied"],
        dependencies={"data": Dependency(input_node.name)},
    )

    approved = BeamTerminate(
        name="approved",
        return_status="approved",
        dependencies={"condition": Dependency(branch.name, "approved")},
    )
    denied = BeamTerminate(
        name="denied",
        return_status="denied",
        dependencies={"condition": Dependency(branch.name, "denied")},
    )

    with beam.Pipeline(options=PipelineOptions()) as pipeline:
        input_data = pipeline | "Read Input" >> ReadRemoteCSV(
            source="gs://vulkan-dev-beam-temp/input_data.csv",
            schema={"tax_id": str, "score": int},
        )
        collections = {INPUT_NODE: input_data}

        result = build_pipeline(pipeline, collections, [branch, approved, denied])
        result | "Print" >> beam.Map(print)


def test_write_to_gcs():
    input_node = BeamInput(
        name=INPUT_NODE,
        schema={"tax_id": str, "score": int},
        source="gs://vulkan-dev-beam-temp/input_data.csv",
    )

    def _branch(data):
        print(data)
        if data["score"] > 500:
            return "approved"
        return "denied"

    branch = BeamBranch(
        name="branch",
        func=_branch,
        outputs=["approved", "denied"],
        dependencies={"data": Dependency(input_node.name)},
    )

    approved = BeamTerminate(
        name="approved",
        return_status="approved",
        dependencies={"condition": Dependency(branch.name, "approved")},
    )
    denied = BeamTerminate(
        name="denied",
        return_status="denied",
        dependencies={"condition": Dependency(branch.name, "denied")},
    )
    filepath = "gs://vulkan-dev-beam-temp/output"
    schema = {"key": str, "status": str, input_node.name: input_node.schema}
    pa_schema = to_pyarrow_schema(schema)

    with beam.Pipeline(options=PipelineOptions()) as pipeline:
        input_data = pipeline | "Read Input" >> ReadParquet(
            source_path=input_node.source,
            schema={"tax_id": str, "score": int},
        )
        input_data | "Print" >> beam.Map(print)
        collections = {INPUT_NODE: input_data}

        result = build_pipeline(pipeline, collections, [branch, approved, denied])
        (
            result
            | beam.ParDo(ProcessResultFn())
            | beam.io.WriteToParquet(filepath, pa_schema)
        )


if __name__ == "__main__":
    test_write_to_gcs()

import apache_beam as beam
import numpy as np
import unittest
import typing

from apache_beam.dataframe.io import read_csv
from apache_beam.dataframe import convert
from apache_beam.runners.render import RenderRunner
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to
from vulkan_public.spec.dependency import Dependency, INPUT_NODE

from vulkan.beam.nodes import BeamInput, BeamTransform, BeamBranch, BeamTerminate
from vulkan.beam.pipeline import make_beam_pipeline, build_pipeline, make_element_key


def test_beam_transform():
    entry = BeamInput(
        name="Input Node",
        description="Input Node",
        schema={"number": int},
    )
    add_one = BeamTransform(
        name="add_one",
        description="Add one",
        func=lambda entry: entry["number"] + 1,
        dependencies={"x": Dependency(entry.name)},
    )
    log = BeamTransform(
        name="log",
        description="Log",
        func=lambda x: np.log(x) if x > 0 else 0,
        dependencies={"x": Dependency(add_one.name)},
    )
    double = BeamTransform(
        name="double",
        description="Double",
        func=lambda x: x * 2,
        dependencies={"x": Dependency(log.name)},
    )
    entries = [{"number": i} for i in range(1, 5)]

    with TestPipeline() as p:
        inputs = p | beam.Create(entries)
        output = (
            inputs
            | "Add one" >> add_one.transform()
            | "Log" >> log.transform()
            | "Double" >> double.transform()
        )
        assert_that(output, equal_to([np.log((x + 1)) * 2 for x in range(1, 5)]))


def test_fan_in():
    entry = BeamInput(
        name="Input Node",
        description="Input Node",
        schema={"number": int},
    )
    add_one = BeamTransform(
        name="add_one",
        description="Add one",
        func=lambda entry: (entry["number"], entry["number"] + 1),
        dependencies={"x": Dependency(entry.name)},
    )
    add_two = BeamTransform(
        name="add_two",
        description="Add two",
        func=lambda entry: (entry["number"], entry["number"] + 2),
        dependencies={"x": Dependency(entry.name)},
    )
    add_three = BeamTransform(
        name="add_three",
        description="Add three",
        func=lambda entry: (entry["number"], entry["number"] + 3),
        dependencies={"x": Dependency(entry.name)},
    )

    def _fan_in(element):
        return {k: v[0] for k, v in element.items()}

    fan_in = BeamTransform(
        name="fan_in",
        description="Fan In",
        func=_fan_in,
        dependencies={
            "x_p1": Dependency(add_one.name),
            "x_p2": Dependency(add_two.name),
            "x_p3": Dependency(add_three.name),
        },
    )

    def _log(x):
        return np.log(x) if x > 0 else 0

    def _sum_logs(element):
        return _log(element["x_p1"]) + _log(element["x_p2"]) + _log(element["x_p3"])

    log = BeamTransform(
        name="log",
        description="Log",
        func=_sum_logs,
        dependencies={"x": Dependency(fan_in.name)},
    )
    double = BeamTransform(
        name="double",
        description="Double",
        func=lambda x: x * 2,
        dependencies={"x": Dependency(log.name)},
    )
    entries = [{"number": i} for i in range(1, 5)]

    with TestPipeline() as p:
        inputs = p | beam.Create(entries)
        x_p1 = inputs | add_one.name >> add_one.transform()
        x_p2 = inputs | add_two.name >> add_two.transform()
        x_p3 = inputs | add_three.name >> add_three.transform()
        (
            {"x_p1": x_p1, "x_p2": x_p2, "x_p3": x_p3}
            | "Group" >> beam.CoGroupByKey()
            | fan_in.name >> fan_in.transform()
            | log.name >> log.transform()
            | double.name >> double.transform()
            | "Print" >> beam.Map(print)
        )
        result = p.run()
        result.wait_until_finish()
        print(result)
        # assert_that(output, equal_to([np.log((x + 1)) * 2 for x in range(1, 5)]))


def test_pipeline():
    input_node = BeamInput(
        name=INPUT_NODE,
        description="Input Node",
        schema={"number": int},
    )

    def _branch(data):
        if data["score"] > 500:
            return "approved"
        return "denied"

    branch = BeamBranch(
        name="branch",
        description="Branch",
        func=_branch,
        outputs=["approved", "denied"],
        dependencies={"x": Dependency(input_node.name)},
    )

    def _fan_in(element):
        (key, values) = element
        return {k: v[0] for k, v in values.items()}

    # entries = [(i, {"tax_id": i}) for i in range(1, 5)]
    data = [(i, {"tax_id": i, "score": i * 200}) for i in range(1, 5)]

    with TestPipeline() as p:
        # inputs = p | beam.Create(entries)
        data = p | beam.Create(data)

        branched = data | branch.name >> branch.branch()

        approved = (
            branched
            | "approved" >> beam.Filter(lambda x: x[1] == "approved")
            | "term. approved" >> beam.Map(lambda x: (x[0], {"status": "approved"}))
        )
        denied = (
            branched
            | "denied" >> beam.Filter(lambda x: x[1] == "denied")
            | "term. denied" >> beam.Map(lambda x: (x[0], {"status": "denied"}))
        )

        ((approved, denied) | "Flatten" >> beam.Flatten() | "Print" >> beam.Map(print))
        result = p.run()
        result.wait_until_finish()


def test_build_pipeline():
    input_node = BeamInput(
        name=INPUT_NODE,
        description="Input Node",
        schema={"number": int},
        source="vulkan/beam/test/input_data.csv",
    )

    def _branch(data):
        if data["score"] > 500:
            return "approved"
        return "denied"

    branch = BeamBranch(
        name="branch",
        description="Branch",
        func=_branch,
        outputs=["approved", "denied"],
        dependencies={"data": Dependency(input_node.name)},
    )

    approved = BeamTerminate(
        name="approved",
        description="Approved",
        return_status="approved",
        dependencies={"condition": Dependency(branch.name, "approved")},
    )
    denied = BeamTerminate(
        name="denied",
        description="Denied",
        return_status="denied",
        dependencies={"condition": Dependency(branch.name, "denied")},
    )

    # with beam.Pipeline(
    #     runner=RenderRunner(),
    #     options=beam.options.pipeline_options.PipelineOptions(),
    # ) as p:
    with TestPipeline() as p:
        pipe = build_pipeline(p, input_node, [branch, approved, denied])
        (pipe | "Print" >> beam.Map(print))

        # result = p.run()
        # result.wait_until_finish()


if __name__ == "__main__":
    test_build_pipeline()

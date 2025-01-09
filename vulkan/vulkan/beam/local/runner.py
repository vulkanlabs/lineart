import json
import os
from abc import ABC, abstractmethod
from time import time

import graphviz
import pyarrow.parquet as pq
from apache_beam.options.pipeline_options import PipelineOptions
from vulkan_public.schemas import DataSourceSpec
from vulkan_public.spec.policy import PolicyDefinition

from vulkan.beam.pipeline import LOCAL_RESULTS_FILE_NAME, BeamPipelineBuilder


class RunResult(ABC):
    @property
    @abstractmethod
    def data(self):
        pass

    @property
    @abstractmethod
    def metadata(self):
        pass

    @abstractmethod
    def get_output(self):
        pass


class SingleRunResult(RunResult):
    def __init__(self, output_path):
        self.output_path = output_path

    @property
    def data(self):
        return self.get_output()

    @property
    def metadata(self):
        pass

    def get_output(self):
        output_path = os.path.join(self.output_path, LOCAL_RESULTS_FILE_NAME)
        with open(output_path, "r") as fp:
            results = json.load(fp)

        return results[1]


class BatchRunResult(RunResult):
    def __init__(self, output_path):
        self.output_path = output_path

    @property
    def data(self):
        return self.get_output()

    @property
    def metadata(self):
        pass

    def get_output(self):
        dataset = pq.ParquetDataset(self.output_path)
        return dataset.read().to_pandas()


class PolicyRunner:
    def __init__(self, policy: PolicyDefinition, staging_path: str):
        self.policy = policy
        self.staging_path = staging_path

    def run(
        self,
        input_data: dict,
        data_sources: list[DataSourceSpec] | None = None,
        config_variables: dict | None = None,
    ) -> RunResult:
        run_id = str(time()).replace(".", "")
        output_path = os.path.join(self.staging_path, run_id)

        builder = get_pipeline_builder(
            policy=self.policy,
            data_sources=data_sources,
            output_path=output_path,
            config_variables=config_variables,
        )

        options = PipelineOptions(["--runner=DirectRunner"])
        pipeline = builder.build_single_run_pipeline(
            input_data=input_data, pipeline_options=options
        )
        pipeline.run()

        return SingleRunResult(output_path)

    def run_batch(
        self,
        input_data_path: str,
        data_sources: list[DataSourceSpec] | None = None,
        config_variables: dict | None = None,
        run_id: str | None = None,
    ) -> BatchRunResult:
        if run_id is None:
            run_id = str(time()).replace(".", "")
        output_path = os.path.join(self.staging_path, run_id)

        builder = get_pipeline_builder(
            policy=self.policy,
            data_sources=data_sources,
            output_path=output_path,
            config_variables=config_variables,
        )

        options = PipelineOptions(["--runner=DirectRunner"])
        pipeline = builder.build_batch_pipeline(
            backfill_id=run_id,
            input_data_path=input_data_path,
            pipeline_options=options,
        )
        pipeline.run()

        return BatchRunResult(output_path)

    def graph(self):
        dot = graphviz.Digraph()

        for node in self.policy.flattened_nodes:
            dot.node(node.name)

        for node, deps in self.policy.flattened_dependencies.items():
            if deps:
                for _, dep in deps.items():
                    dot.edge(dep.node, node)

        return dot


def get_pipeline_builder(
    policy,
    data_sources: list[DataSourceSpec],
    output_path: str,
    config_variables: dict[str, str] | None = None,
):
    if config_variables is None:
        config_variables = {}

    data_sources_map = {}
    for source in data_sources:
        assert isinstance(
            source, DataSourceSpec
        ), f"Data sources should be an instance of DataSourceSpec, got {source}"
        if source.name in data_sources_map:
            raise ValueError(f"Duplicate data source name: {source.name}")
        data_sources_map[source.name] = source

    builder = BeamPipelineBuilder(
        policy=policy,
        output_path=output_path,
        data_sources=data_sources_map,
        config_variables=config_variables,
    )
    return builder

import json
from argparse import ArgumentParser

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.pipeline import Pipeline

from vulkan.core.backtest.metrics import MetricsMetadata, Target, TargetKind
from vulkan.runners.beam.io import ReadParquet
from vulkan.runners.beam.metrics.binary import BinaryDistributionTransform


def build_metrics_pipeline(
    input_data_path: str,
    results_data_path: str,
    output_path: str,
    metrics_metadata: MetricsMetadata,
    pipeline_options: PipelineOptions,
) -> Pipeline:
    group_by_cols = [
        "backfill_id",
        metrics_metadata.outcome,
    ]
    if metrics_metadata.time is not None:
        group_by_cols.append(metrics_metadata.time)
    if metrics_metadata.groups is not None:
        group_by_cols.extend(metrics_metadata.groups)

    metrics_transform = _make_metrics_transform(
        target=metrics_metadata.target,
        group_by_cols=group_by_cols,
    )

    p = beam.Pipeline(options=pipeline_options)
    input_data = p | "Read Input Data" >> ReadParquet(input_data_path)
    results_data = (
        p
        | "Read Results Data" >> beam.io.ReadFromParquet(results_data_path)
        | beam.Map(lambda x: (x["key"], x))
    )
    data = {
        "results_data": results_data,
        "input_data": input_data,
    } | "Join Data" >> beam.CoGroupByKey()

    (
        data
        | "Select Relevant Columns"
        >> ExtractRelevantColumns(
            backfill_id_column="backfill_id",
            outcome_column=metrics_metadata.outcome,
            target_column=metrics_metadata.target.name,
            time_column=metrics_metadata.time,
            group_by_columns=metrics_metadata.groups,
        )
        | "Calculate Metrics" >> metrics_transform
        | "Enforce Schema" >> beam.Select(*metrics_transform.output_columns())
        | "Write Metrics"
        >> beam.io.WriteToJson(
            output_path,
            num_shards=1,
            file_naming=beam.io.fileio.single_file_naming(
                prefix="metrics", suffix=".json"
            ),
        )
    )

    return p


class ExtractRelevantColumns(beam.PTransform):
    def __init__(
        self,
        backfill_id_column: str,
        outcome_column: str,
        target_column: str,
        time_column: str | None,
        group_by_columns: list[str] | None,
    ):
        self.backfill_id_column = backfill_id_column
        self.target_column = target_column
        self.outcome_column = outcome_column
        self.time_column = time_column
        self.group_by_columns = group_by_columns

        _input_data_columns = [target_column]
        if time_column is not None:
            _input_data_columns.append(time_column)
        if group_by_columns is not None:
            _input_data_columns.extend(group_by_columns)
        self._input_data_columns = _input_data_columns

    def expand(self, pcoll):
        return pcoll | "Create Working Frame" >> beam.FlatMap(
            _extract_columns_by_key,
            input_data_columns=self._input_data_columns,
            outcome_column=self.outcome_column,
            backfill_id_column=self.backfill_id_column,
        )


def _extract_columns_by_key(
    element: tuple,
    input_data_columns: list[str],
    outcome_column: str,
    backfill_id_column: str,
):
    key = element[0]
    data = element[1]

    input_data_dict = {col: data["input_data"][0][col] for col in input_data_columns}

    results = []
    for backfill_results in data["results_data"]:
        results_dict = {"key": key, **input_data_dict}

        results_dict[outcome_column] = backfill_results[outcome_column]
        results_dict[backfill_id_column] = backfill_results[backfill_id_column]
        results.append(results_dict)

    return [beam.Row(**r) for r in results]


def _make_metrics_transform(
    target: Target,
    group_by_cols: list[str],
) -> beam.PTransform:
    if target.kind == TargetKind.BINARY_DISTRIBUTION:
        return BinaryDistributionTransform(
            target=target,
            group_by_cols=group_by_cols,
        )
    raise NotImplementedError(f"Unsupported target kind for {Target}")


if __name__ == "__main__":
    parser = ArgumentParser()
    # Application-defined
    parser.add_argument("--input_data_path", type=str, help="Path to input data")
    parser.add_argument("--results_data_path", type=str, help="Path to results data")
    parser.add_argument("--output_path", type=str, help="Path to save metrics")
    parser.add_argument("--outcome", type=str, help="Name of the outcome column")
    parser.add_argument(
        "--target_kind", type=str, help="Kind of target, such as BINARY_DISTRIBUTION"
    )
    # User-defined
    parser.add_argument("--target_name", type=str, help="Name of the target column")
    parser.add_argument(
        "--time",
        type=str,
        default=None,
        required=False,
        help="Column that indicates time",
    )
    parser.add_argument(
        "--groups",
        type=str,
        default=None,
        required=False,
        help="Array of columns used to group metrics",
    )

    pipeline_args, unknown_args = parser.parse_known_args()
    target = Target(
        name=pipeline_args.target_name, kind=TargetKind(pipeline_args.target_kind)
    )

    groups = None
    if pipeline_args.groups is not None:
        groups = json.loads(pipeline_args.groups)

    args_pipeline_options = [
        "--save_main_session",
        "--sdk_location",
        "container",
        *unknown_args,
    ]

    metrics_metadata = MetricsMetadata(
        outcome=pipeline_args.outcome,
        target=target,
        time=pipeline_args.time,
        groups=groups,
    )
    pipeline_options = PipelineOptions(args_pipeline_options)

    build_metrics_pipeline(
        input_data_path=pipeline_args.input_data_path,
        results_data_path=pipeline_args.results_data_path,
        output_path=pipeline_args.output_path,
        metrics_metadata=metrics_metadata,
        pipeline_options=pipeline_options,
    ).run().wait_until_finish()

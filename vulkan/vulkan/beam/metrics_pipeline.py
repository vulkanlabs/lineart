import json
from argparse import ArgumentParser

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.pipeline import Pipeline

from vulkan.backtest.metrics import MetricsMetadata, Target, TargetKind
from vulkan.beam.metrics.binary import BinaryDistributionTransform


def build_metrics_pipeline(
    results_data: str,
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
    (
        p
        | "Read Results Data" >> beam.io.ReadFromCsv(results_data)
        | "With Metrics" >> metrics_transform
        | "With Schema" >> beam.Select(*metrics_transform.output_columns())
        | "Write Metrics" >> beam.io.WriteToJson("metrics.json")
    )

    return p


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
    parser.add_argument("--results_data", type=str, help="Path to results data")
    parser.add_argument("--outcome", type=str, help="Name of the outcome column")
    parser.add_argument("--target_name", type=str, help="Name of the target column")
    parser.add_argument(
        "--target_kind", type=str, help="Kind of target, such as BINARY_DISTRIBUTION"
    )
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
    target = Target(name=pipeline_args.target_name, kind=TargetKind(pipeline_args.target_kind))

    groups = None
    if pipeline_args.groups is not None:
        groups = json.loads(pipeline_args.groups)

    args_pipeline_options = [
        "--save_main_session"
        "--sdk_location", "container",
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
        pipeline_args.results_data,
        metrics_metadata,
        pipeline_options,
    ).run().wait_until_finish()

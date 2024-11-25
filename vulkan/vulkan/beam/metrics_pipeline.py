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
    target: Target, group_by_cols: list[str]
) -> beam.PTransform:
    if target.kind == TargetKind.BINARY_DISTRIBUTION:
        return BinaryDistributionTransform(
            target=target,
            group_by_cols=group_by_cols,
        )


if __name__ == "__main__":
    args_results_data = "test/results_data.csv"
    args_pipeline_options = [
        "--runner=DirectRunner",
    ]

    metrics_metadata = MetricsMetadata(
        outcome="status",
        target=Target(name="default", kind=TargetKind.BINARY_DISTRIBUTION),
        time="month",
        groups=["group_col"],
    )
    pipeline_options = PipelineOptions(args_pipeline_options)

    build_metrics_pipeline(
        args_results_data, metrics_metadata, pipeline_options
    ).run().wait_until_finish()

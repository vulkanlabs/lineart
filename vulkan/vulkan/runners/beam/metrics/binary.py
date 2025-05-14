import apache_beam as beam
from apache_beam.transforms.combiners import CountCombineFn

from vulkan.core.backtest.metrics import Target


class BinaryDistributionTransform(beam.PTransform):
    """Calculate basic statistics for a binary target.

    When the target is binary, and the outcome is a categorical value
    for which the target distribution is to be calculated.
    """

    def __init__(self, target: Target, group_by_cols: list[str]):
        self.target = target
        self.group_by_cols = group_by_cols

    def expand(self, pcoll):
        return pcoll | "Basic Statistics for Binary Distribution" >> (
            beam.GroupBy(*self.group_by_cols)
            .aggregate_field("key", CountCombineFn(), "count")
            .aggregate_field(lambda x: getattr(x, self.target.name) == 1, sum, "ones")
            .aggregate_field(lambda x: getattr(x, self.target.name) == 0, sum, "zeros")
        )

    def output_columns(self):
        return {
            *self.group_by_cols,
            "count",
            "ones",
            "zeros",
        }

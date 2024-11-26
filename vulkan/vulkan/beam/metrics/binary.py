import apache_beam as beam
from apache_beam.transforms.combiners import CountCombineFn


class BinaryDistributionTransform(beam.PTransform):
    """Calculate basic statistics for a binary target.

    When the target is binary, and the outcome is a categorical value
    for which the target distribution is to be calculated.
    """

    def __init__(self, target, group_by_cols):
        self.target = target
        self.group_by_cols = group_by_cols

    def expand(self, pcoll):
        return pcoll | "Basic Statistics" >> (
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

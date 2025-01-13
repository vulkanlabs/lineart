# class BinaryClassificationMetricsTransform(beam.PTransform):
#     """

#     When the target is binary and the outcome is an estimate of that.
#     """

#     def __init__(
#         self,
#         target: Target,
#         group_by_cols: list[str],
#         y_pred: str = "y_pred",
#         y_true: str = "y_true",
#     ):
#         self.y_pred = y_pred
#         self.y_true = y_true
#         self.group_by_cols = group_by_cols
#         self.target = target

#     def expand(self, pcoll):
#         return (
#             pcoll
#             | "As Dict" >> beam.Map(lambda x: x._asdict())
#             | "Map Targets"
#             >> beam.Map(
#                 _map_target,
#                 target_spec=self.target.spec,
#                 from_col=self.target.name,
#                 to_col=self.y_true,
#             )
#             | "Map Outcomes"
#             >> beam.Map(
#                 _map_target,
#                 target_spec=self.target.spec,
#                 from_col="status",
#                 to_col=self.y_pred,
#             )
#             | "Mark Outcomes"
#             >> beam.Map(_mark_outcome, y_pred=self.y_pred, y_true=self.y_true)
#             | "Group By"
#             >> (
#                 beam.GroupBy()
#                 .aggregate_field(lambda x: x[_TP], sum, _TP)
#                 .aggregate_field(lambda x: x[_FP], sum, _FP)
#                 .aggregate_field(lambda x: x[_FN], sum, _FN)
#                 .aggregate_field(lambda x: x[_TN], sum, _TN)
#                 .aggregate_field(lambda x: x["key"], CountCombineFn(), _COUNT)
#             )
#             | "Groups As Dict" >> beam.Map(lambda x: x._asdict())
#             | "With Precision" >> beam.Map(_with_precision, true_pos=_TP, false_pos=_FP)
#             | "With Recall" >> beam.Map(_with_recall, true_pos=_TP, false_neg=_FN)
#             | "Remove Intermediate Columns"
#             >> beam.Select(
#                 **{
#                     "precision": lambda x: x["precision"],
#                     "recall": lambda x: x["recall"],
#                     "count": lambda x: x[_COUNT],
#                     **{col: lambda x: x[col] for col in self.group_by_cols},
#                 }
#             )
#         )


# _COUNT = "count__"
# _TP = "tp__"
# _FP = "fp__"
# _FN = "fn__"
# _TN = "tn__"


# def _with_precision(row, true_pos: str, false_pos: str):
#     denom = row[true_pos] + row[false_pos]
#     if denom == 0:
#         row["precision"] = NaN
#     else:
#         row["precision"] = row[true_pos] / denom
#     return row


# def _with_recall(row, true_pos: str, false_neg: str):
#     denom = row[true_pos] + row[false_neg]
#     if denom == 0:
#         row["recall"] = NaN
#     else:
#         row["recall"] = row[true_pos] / denom
#     return row


# def _mark_outcome(row, y_pred: str, y_true: str):
#     y_true = row[y_true]
#     y_pred = row[y_pred]

#     row[_TP] = 0
#     row[_FP] = 0
#     row[_FN] = 0
#     row[_TN] = 0

#     if y_true and y_pred:
#         row[_TP] = 1
#     elif not y_true and y_pred:
#         row[_FP] = 1
#     elif y_true and not y_pred:
#         row[_FN] = 1
#     else:
#         row[_TN] = 1
#     return row


# def _map_target(row, target_spec: TargetBinary, from_col: str, to_col: str):
#     row[to_col] = target_spec.get_value(row[from_col])
#     return row

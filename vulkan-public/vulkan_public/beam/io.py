import csv
import hashlib
import json
from functools import partial

import apache_beam as beam
import pyarrow as pa
from apache_beam.dataframe import convert
from apache_beam.dataframe.io import read_csv


class ReadParquet(beam.PTransform):
    def __init__(self, data_path: str):
        self.data_path = data_path

    def expand(self, pcoll):
        return (
            pcoll
            | "Read File" >> beam.io.ReadFromParquet(self.data_path)
            | "Make Key" >> beam.Map(_make_element_key)
        )


class ReadRemoteCSV(beam.PTransform):
    def __init__(self, data_path: str, schema: dict[str, type] | None = None):
        self.data_path = data_path
        self.csv_parser = partial(parse_csv_line, schema)

    def expand(self, pcoll):
        return (
            pcoll
            | "Read File" >> beam.io.ReadFromText(self.data_path, skip_header_lines=1)
            | "Parse CSV" >> beam.Map(self.csv_parser)
            | "Make Key" >> beam.Map(_make_element_key)
        )


def parse_csv_line(schema, line):
    """Parse a single line of CSV into a dictionary."""
    reader = csv.reader([line])
    fields = list(schema.keys())
    data = dict(zip(fields, next(reader)))
    return {k: schema[k](v) for k, v in data.items()}


class ReadLocalCSV(beam.PTransform):
    def __init__(self, source: str):
        self.source = source

    def expand(self, pcoll):
        dataframe = pcoll | "Read Source" >> read_csv(self.source)
        return (
            convert.to_pcollection(dataframe)
            | "To dictionaries" >> beam.Map(lambda x: dict(x._asdict()))
            | "Make Key" >> beam.Map(_make_element_key)
        )


def _make_element_key(element: dict) -> tuple[str, dict]:
    content = json.dumps(element, sort_keys=True)
    key = hashlib.md5(content.encode("utf-8")).hexdigest()
    return (key, element)


class ProcessResultFn(beam.DoFn):
    def __init__(self, backfill_id: str) -> None:
        self.backfill_id = backfill_id

    def process(self, element, **kwargs):
        result = {}
        key, value = element
        result["backfill_id"] = self.backfill_id
        result["key"] = key
        result["status"] = value["result"][0]["status"]
        result.update({k: v[0] for k, v in value.items() if k != "result"})
        yield result


class WriteParquet(beam.PTransform):
    def __init__(self, filepath: str, schema: dict[str, type], backfill_id: str):
        self.filepath = filepath
        self.schema = to_pyarrow_schema(schema)
        self.backfill_id = backfill_id

    def expand(self, pcoll):
        return (
            pcoll
            | "Process Result" >> beam.ParDo(ProcessResultFn(self.backfill_id))
            | "Write to Parquet" >> beam.io.WriteToParquet(self.filepath, self.schema)
        )


def to_pyarrow_schema(schema: dict[str, type]) -> dict[str, str]:
    fields = [to_pyarrow_field(name, dtype) for name, dtype in schema.items()]
    return pa.schema(fields)


def to_pyarrow_field(name, dtype):
    if isinstance(dtype, dict):
        # Handle nested structure (dict) by recursively converting fields
        nested_fields = [to_pyarrow_field(k, v) for k, v in dtype.items()]
        return pa.field(name, pa.struct(nested_fields))

    if isinstance(dtype, list):
        # Handle list types (e.g., list of strings).
        # Currently assuming a list of a single primitive type.
        # TODO: add support for more complex nested structures.
        element_type = _PYARROW_TYPE_MAPPING[dtype[0]]
        return pa.field(name, pa.list(element_type))

    # Directly map primitive types
    return pa.field(name, _PYARROW_TYPE_MAPPING[dtype])


_PYARROW_TYPE_MAPPING = {
    int: pa.int64(),
    float: pa.float64(),
    str: pa.string(),
    bool: pa.bool_(),
}

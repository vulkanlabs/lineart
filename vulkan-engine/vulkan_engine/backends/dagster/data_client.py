import pickle
from dataclasses import dataclass

import sqlalchemy
from dagster._core.events.log import EventLogEntry
from sqlalchemy import create_engine

from vulkan_engine.backends.data_client import PYTHON_LOG_LEVELS, BaseDataClient
from vulkan_engine.schemas import LogEntry, StepDetails, StepMetadataBase


@dataclass
class DagsterDatabaseConfig:
    """Configuration for the Dagster database."""

    user: str
    password: str
    host: str
    port: str
    database: str

    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string for Dagster."""
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class DagsterDataClient(BaseDataClient):
    def __init__(self, config: DagsterDatabaseConfig):
        self.dagster_db = create_engine(config.connection_string, echo=False)

    def get_run_data(self, run_id: str) -> dict[str, StepDetails]:
        # Get step outputs from Dagster database
        with self.dagster_db.connect() as conn:
            q = sqlalchemy.text(
                """
            SELECT step_name, object_name, value
              FROM objects
             WHERE run_id = :run_id
            """
            )
            results = conn.execute(q, {"run_id": run_id}).fetchall()

        # Get event logs to compute metadata
        with self.dagster_db.connect() as conn:
            q = sqlalchemy.text(
                """
            SELECT step_key, event
              FROM event_logs
             WHERE run_id = :run_id
               AND step_key IS NOT NULL
            """
            )
            event_logs = conn.execute(q, {"run_id": run_id}).fetchall()

        # Process outputs
        results_by_name = {result[0]: (result[1], result[2]) for result in results}

        # Compute metadata from event logs
        metadata = self._compute_metadata_from_events(event_logs)

        step_details: dict[str, StepDetails] = {}

        # Combine outputs with metadata
        all_step_names = set(results_by_name.keys()) | set(metadata.keys())

        for step_name in all_step_names:
            value = None

            if step_name in results_by_name:
                object_name, raw_value = results_by_name[step_name]
                if object_name != "result":
                    # Branch node output - object_name represents the path taken
                    value = object_name
                else:
                    # Unpickle the actual result
                    try:
                        value = pickle.loads(raw_value)
                    except pickle.UnpicklingError:
                        raise Exception(
                            f"Failed to unpickle data for {step_name}.{object_name}"
                        )

            step_metadata = metadata.get(step_name)
            step_details[step_name] = {"output": value, "metadata": step_metadata}

        return step_details

    def _compute_metadata_from_events(
        self, event_logs: list
    ) -> dict[str, StepMetadataBase]:
        """Compute step metadata from Dagster event logs."""
        step_events = {}

        for step_key, event_json in event_logs:
            parsed_event = EventLogEntry.from_json(event_json)

            if not parsed_event.is_dagster_event:
                continue

            event_type = parsed_event.dagster_event_type

            if step_key not in step_events:
                step_events[step_key] = {
                    "start_time": None,
                    "end_time": None,
                    "node_type": "",
                    "error": None,
                }

            # Track step start
            if event_type == "STEP_START":
                step_events[step_key]["start_time"] = parsed_event.timestamp

            # Track step completion
            elif event_type == "STEP_SUCCESS":
                step_events[step_key]["end_time"] = parsed_event.timestamp

            # Track step failure
            elif event_type == "STEP_FAILURE":
                step_events[step_key]["end_time"] = parsed_event.timestamp
                if parsed_event.dagster_event:
                    step_events[step_key]["error"] = str(
                        parsed_event.dagster_event.event_specific_data
                    )

        # Convert to StepMetadataBase objects
        metadata = {}
        for step_name, events in step_events.items():
            if events["start_time"] is not None and events["end_time"] is not None:
                metadata[step_name] = StepMetadataBase(
                    step_name=step_name,
                    node_type=events["node_type"],
                    start_time=events["start_time"],
                    end_time=events["end_time"],
                    error=events["error"],
                )

        return metadata

    def get_run_logs(self, run_id: str) -> list[LogEntry]:
        with self.dagster_db.connect() as conn:
            q = sqlalchemy.text("""
            SELECT timestamp,
                   step_key,
                   event
              FROM event_logs
             WHERE run_id = :run_id
            """)

            logs = conn.execute(q, {"run_id": run_id}).fetchall()

        if len(logs) == 0:
            return []

        processed_logs = []
        for entry in logs:
            try:
                processed_entry = _process_log_entry(entry)
            except ValueError as e:
                msg = f"Error retrieving logs for run {run_id}: {e}"
                raise ValueError(msg)

            if processed_entry is not None:
                processed_logs.append(processed_entry)

        return processed_logs


def _process_log_entry(entry) -> LogEntry:
    timestamp, step_key, event = entry
    parsed_event = EventLogEntry.from_json(event)
    event_source = "DAGSTER" if parsed_event.is_dagster_event else "USER"

    if event_source == "USER":
        message = parsed_event.user_message
        log_level = parsed_event.level
        if isinstance(log_level, int):
            log_level = PYTHON_LOG_LEVELS[log_level]

        event_content = {
            "log_type": "LOG",
            "message": message,
            "level": log_level,
        }
    elif event_source == "DAGSTER":
        event_content = {
            "log_type": parsed_event.dagster_event_type,
            "message": parsed_event.message,
            # For future reference, `parsed_event` is an instance of `EventLogEntry`
            # containing a `dagster_event` attribute. At the time, we won't
            # use any of the event-specific data.
            # "content": parsed_event.to_json(),
        }
    else:
        raise ValueError(f"Unknown event source: {event_source}")

    return LogEntry(
        timestamp=timestamp,
        step_key=step_key,
        source=event_source,
        event=event_content,
    )

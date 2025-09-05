import sqlalchemy
from dagster._core.events.log import EventLogEntry
from dagster_graphql import DagsterGraphQLClient
from sqlalchemy import create_engine

from vulkan_engine.config import DagsterDatabaseConfig, DagsterServiceConfig
from vulkan_engine.backends.dagster.trigger_run import create_dagster_client
from vulkan_engine.schemas import LogEntry


def create_dagster_client_from_config(
    config: DagsterServiceConfig,
) -> DagsterGraphQLClient:
    """Create Dagster client from configuration."""
    try:
        port = int(config.port)
    except ValueError:
        raise ValueError("Dagster port must be an integer")

    return create_dagster_client(config.host, port)


class DagsterDataClient:
    def __init__(self, config: DagsterDatabaseConfig):
        self.engine = create_engine(config.connection_string, echo=True)

    def get_run_data(self, run_id: str) -> list[tuple[str, str, str]]:
        with self.engine.connect() as conn:
            q = sqlalchemy.text(
                """
            SELECT step_name, object_name, value
              FROM objects
             WHERE run_id = :run_id
            """
            )
            results = conn.execute(q, {"run_id": run_id}).fetchall()
        return results

    def get_run_logs(self, run_id: str) -> list[LogEntry]:
        with self.engine.connect() as conn:
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
            log_level = _PYTHON_LOG_LEVELS[log_level]

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

    return {
        "timestamp": timestamp,
        "step_key": step_key,
        "source": event_source,
        "event": event_content,
    }


_PYTHON_LOG_LEVELS = {
    10: "DEBUG",
    20: "INFO",
    30: "WARNING",
    40: "ERROR",
    50: "CRITICAL",
}


def create_dagster_data_client(config: DagsterDatabaseConfig) -> DagsterDataClient:
    """Create DagsterDataClient from configuration."""
    return DagsterDataClient(config)

import os

import sqlalchemy
from sqlalchemy import Engine, create_engine

from vulkan_server.dagster.trigger_run import create_dagster_client


def get_dagster_client():
    # TODO: receive as env
    DAGSTER_URL = "dagster"
    DAGSTER_PORT = 3000
    dagster_client = create_dagster_client(DAGSTER_URL, DAGSTER_PORT)
    return dagster_client


def _get_dagster_db() -> Engine:
    DAGSTER_DB_USER = os.getenv("DAGSTER_DB_USER")
    DAGSTER_DB_PASSWORD = os.getenv("DAGSTER_DB_PASSWORD")
    DAGSTER_DB_HOST = os.getenv("DAGSTER_DB_HOST")
    DAGSTER_DB_PORT = os.getenv("DAGSTER_DB_PORT")
    DAGSTER_DB_DATABASE = os.getenv("DAGSTER_DB_DATABASE")
    if (
        DAGSTER_DB_USER is None
        or DAGSTER_DB_PASSWORD is None
        or DAGSTER_DB_HOST is None
        or DAGSTER_DB_PORT is None
        or DAGSTER_DB_DATABASE is None
    ):
        raise ValueError(
            "Please set the following environment variables: "
            "DAGSTER_DB_USER, DAGSTER_DB_PASSWORD, DAGSTER_DB_HOST, DAGSTER_DB_PORT, DAGSTER_DB_DATABASE"
        )

    connection_str = f"postgresql+psycopg2://{DAGSTER_DB_USER}:{DAGSTER_DB_PASSWORD}@{DAGSTER_DB_HOST}:{DAGSTER_DB_PORT}/{DAGSTER_DB_DATABASE}"
    engine = create_engine(connection_str, echo=True)
    # DBSession = sessionmaker(bind=engine)

    return engine


class DagsterDataClient:
    def __init__(self):
        self.engine = _get_dagster_db()

    def get_run_data(self, run_id: str):
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

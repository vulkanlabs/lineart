from dataclasses import asdict, dataclass
from pickle import dumps, loads
from typing import Any

import requests
from dagster import InputContext, IOManager, OutputContext
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.sql import text

from vulkan.core.step_metadata import StepMetadata
from vulkan.runners.dagster.run_config import RUN_CONFIG_KEY, VulkanRunConfig

PUBLISH_IO_MANAGER_KEY = "publish_metadata_io_manager"
METADATA_OUTPUT_KEY = "metadata"


class PostgreSQLIOManager(IOManager):
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        table: str,
        run_id: str,
    ):
        self.table = table
        self.run_id = run_id

        url = URL.create(
            "postgresql+psycopg2",
            password=password,
            username=user,
            host=host,
            port=port,
            database=database,
        )
        self.engine = create_engine(url)

    def handle_output(self, context: OutputContext, obj: Any) -> None:
        try:
            data = dumps(obj)
        except Exception as e:
            raise ValueError(f"Failed to pickle data: {obj}") from e

        query_str = text(
            f"""
            INSERT INTO {self.table}
            (run_id, step_name, object_name, value)
            VALUES (:run_id, :step_name, :object_name, :value)
            """
        )
        with self.engine.connect() as conn:
            conn.execute(
                query_str,
                {
                    "run_id": self.run_id,
                    "step_name": context.step_key,
                    "object_name": context.name,
                    "value": data,
                },
            )
            conn.commit()

    def load_input(self, context: InputContext) -> Any:
        query_str = text(
            f"""
            SELECT value FROM {self.table}
             WHERE run_id = :run_id
               AND step_name = :step_name 
               AND object_name = :object_name
               """
        )
        with self.engine.connect() as conn:
            result = conn.execute(
                query_str,
                {
                    "run_id": self.run_id,
                    "step_name": context.upstream_output.step_key,
                    "object_name": context.upstream_output.name,
                },
            ).fetchone()
            if not result:
                raise ValueError(f"Data not found for {context.get_identifier()}")
            return loads(bytes(result[0]))


@dataclass(frozen=True)
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    object_table: str


DB_CONFIG_KEY = "db_config"
POSTGRES_IO_MANAGER_KEY = "postgres_io_manager"


def postgresql_io_manager(context) -> PostgreSQLIOManager:
    run_config: VulkanRunConfig = getattr(context.resources, RUN_CONFIG_KEY)
    db_config: DBConfig = getattr(context.resources, "db_config")

    return PostgreSQLIOManager(
        host=db_config.host.get_value(),
        port=db_config.port.get_value(),
        user=db_config.user.get_value(),
        password=db_config.password.get_value(),
        database=db_config.database.get_value(),
        table=db_config.object_table.get_value(),
        run_id=run_config.run_id,
    )


class PublishMetadataIOManager(IOManager):
    def __init__(self, url: str):
        self._url = url

    def handle_output(self, context: OutputContext, obj):
        if context.name != "metadata":
            raise NotImplementedError("Currently only supports metadata")

        if not isinstance(obj, StepMetadata):
            raise TypeError(f"Expected StepMetadata, got {type(obj)}")

        try:
            response = requests.post(
                self._url,
                json={
                    "step_name": context.step_key,
                    **asdict(obj),
                },
            )
            if response.status_code != 200:
                msg = f"ERROR {response.status_code}: Failed to publish metadata: {response.text}"
                raise ValueError(msg)
        except Exception as e:
            msg = f"Failed to publish metadata for step {context.get_identifier()}"
            raise ValueError(msg) from e

    def load_input(self, context: InputContext):
        raise NotImplementedError("Currently only supports metadata output")


def metadata_io_manager(context) -> PublishMetadataIOManager:
    run_config: VulkanRunConfig = getattr(context.resources, RUN_CONFIG_KEY)
    run_id = run_config.run_id
    server_url = run_config.server_url
    url = f"{server_url}/runs/{run_id}/metadata"

    return PublishMetadataIOManager(url=url)

from dataclasses import dataclass
from pickle import dumps, loads
from typing import Any

from dagster import InputContext, IOManager, OutputContext
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.sql import text

from vulkan.runners.shared.constants import RUN_CONFIG_KEY
from vulkan.runners.shared.run_config import VulkanRunConfig


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

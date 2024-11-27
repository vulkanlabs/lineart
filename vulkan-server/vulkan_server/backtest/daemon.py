import asyncio
import os

from pydantic.dataclasses import dataclass

from vulkan_server.logger import init_logger


@dataclass
class _BacktestDaemonConfig:
    time_step: int


class BacktestDaemon:
    def __init__(self, config: _BacktestDaemonConfig):
        self.config = config
        self.logger = init_logger("BacktestDaemon")

    async def run_main(self):
        while True:
            await asyncio.sleep(self.config.time_step)
            self.logger.info("Tick") 

    @classmethod
    def from_env(cls) -> "BacktestDaemon":
        cfg = _BacktestDaemonConfig(
            time_step=int(os.getenv("BACKTEST_DAEMON_TIME_STEP", "30"))
        )

        return cls(cfg)

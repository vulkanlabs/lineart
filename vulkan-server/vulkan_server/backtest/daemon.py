import asyncio
import os

from pydantic.dataclasses import dataclass
from vulkan.core.run import RunStatus

from vulkan_server.backtest.launcher import async_get_backtest_job_status, get_launcher
from vulkan_server.db import Backfill, Backtest, BacktestMetrics, get_db
from vulkan_server.logger import init_logger
from vulkan_server.routers.backtests import launch_metrics_job


@dataclass
class _BacktestDaemonConfig:
    time_step: int


_IN_PROGRESS_RUN_STATUS = {RunStatus.PENDING, RunStatus.STARTED}


class BacktestDaemon:
    def __init__(self, config: _BacktestDaemonConfig):
        self.config = config
        self.logger = init_logger("BacktestDaemon")
        self.db = next(get_db())
        self.launcher = get_launcher(db=self.db)

    async def run_main(self):
        while True:
            await asyncio.sleep(self.config.time_step)
            self.logger.info("Tick")
            await self.check_backfills()
            await self.check_metrics_jobs()

    async def check_metrics_jobs(self):
        jobs = (
            self.db.query(BacktestMetrics)
            .filter(BacktestMetrics.status.in_(_IN_PROGRESS_RUN_STATUS))
            .all()
        )
        self.logger.debug(f"Found {len(jobs)} metrics jobs in progress")

        for job in jobs:
            self.logger.debug(f"Checking metrics job {job.metrics_id}")
            status = await async_get_backtest_job_status(job.gcp_job_id)
            if status in _IN_PROGRESS_RUN_STATUS:
                # Still in progress.
                continue

            # When done, mark status.
            job.status = status
            self.db.commit()
            self.logger.debug(f"Metrics job {job.metrics_id} finished with {status=}")

    async def check_backfills(self):
        backfills = (
            self.db.query(Backfill)
            .filter(Backfill.status.in_(_IN_PROGRESS_RUN_STATUS))
            .all()
        )
        self.logger.debug(f"Found {len(backfills)} backfills in progress")

        for backfill in backfills:
            self.logger.debug(f"Checking backfill {backfill.backfill_id}")
            status = await async_get_backtest_job_status(backfill.gcp_job_id)
            if status in _IN_PROGRESS_RUN_STATUS:
                # Still in progress.
                continue

            # When done, mark status and trigger metrics job.
            backfill.status = status
            self.db.commit()
            self.logger.debug(
                f"Backfill {backfill.backfill_id} finished with {status=}"
            )

            backtest = (
                self.db.query(Backtest)
                .filter_by(backtest_id=backfill.backtest_id)
                .first()
            )
            if backtest.calculate_metrics:
                launch_metrics_job(
                    backtest_id=backtest.backtest_id,
                    db=self.db,
                    launcher=self.launcher,
                )
                self.logger.debug(f"Launched metrics job for {backtest.backtest_id}")

    @classmethod
    def from_env(cls) -> "BacktestDaemon":
        cfg = _BacktestDaemonConfig(
            time_step=int(os.getenv("BACKTEST_DAEMON_TIME_STEP", "30"))
        )

        return cls(cfg)

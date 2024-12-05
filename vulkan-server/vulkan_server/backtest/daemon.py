import asyncio
import os

from pydantic.dataclasses import dataclass
from vulkan.core.run import JobStatus, RunStatus

from vulkan_server.backtest.launcher import async_get_backtest_job_status, get_launcher
from vulkan_server.backtest.results import get_results_db
from vulkan_server.db import Backfill, Backtest, BacktestMetrics, get_db
from vulkan_server.logger import init_logger
from vulkan_server.routers.backtests import launch_metrics_job


@dataclass
class _BacktestDaemonConfig:
    time_step: int


class BacktestDaemon:
    def __init__(self, config: _BacktestDaemonConfig):
        self.config = config
        self.logger = init_logger("BacktestDaemon")
        self.db = next(get_db())
        self.launcher = get_launcher(db=self.db)
        self.results_db = get_results_db()

    @classmethod
    def from_env(cls) -> "BacktestDaemon":
        cfg = _BacktestDaemonConfig(
            time_step=int(os.getenv("BACKTEST_DAEMON_TIME_STEP", "30"))
        )

        return cls(cfg)

    async def run_main(self):
        while True:
            await asyncio.sleep(self.config.time_step)
            await self.check_backtests()
            await self.check_metrics_jobs()

    async def check_metrics_jobs(self):
        jobs = (
            self.db.query(BacktestMetrics)
            .filter(BacktestMetrics.status.in_(_IN_PROGRESS_RUN_STATUS))
            .all()
        )
        self.logger.debug(f"Found {len(jobs)} metrics jobs in progress")

        for job in jobs:
            self.logger.debug(f"Checking metrics job {job.backtest_metrics_id}")
            status = await async_get_backtest_job_status(job.gcp_job_id)
            if status in _IN_PROGRESS_RUN_STATUS:
                # Still in progress.
                continue

            job.status = status
            if status == RunStatus.SUCCESS:
                metrics = self.results_db.load_metrics(job.output_path)
                job.metrics = metrics.to_dict(orient="records")

            # When done, mark status and retrieve results.
            self.db.commit()
            self.logger.debug(
                f"Metrics job {job.backtest_metrics_id} finished with {status=}"
            )

    async def check_backtests(self):
        backtests = (
            self.db.query(Backtest)
            .filter(Backtest.status.in_(_IN_PROGRESS_BACKTEST_STATUS))
            .all()
        )
        self.logger.debug(f"Found {len(backtests)} backtests in progress")

        for backtest in backtests:
            self.logger.debug(f"Checking backtest {backtest.backtest_id}")
            pending_jobs = await self._check_backfills(backtest)
            if pending_jobs > 0:
                continue

            # If all backfills are done, mark backtest as done.
            backtest.status = JobStatus.DONE
            self.db.commit()
            self.logger.debug(f"Backtest {backtest.backtest_id} finished")

            if backtest.calculate_metrics and self._backfills_succeeded(backtest):
                launch_metrics_job(
                    backtest_id=str(backtest.backtest_id),
                    db=self.db,
                    launcher=self.launcher,
                )
                self.logger.debug(f"Launched metrics job for {backtest.backtest_id}")

    async def _check_backfills(self, backtest: Backtest) -> int:
        """Checks each backfill job in a backtest.

        Returns
        -------
        int
            Number of pending backfill jobs.

        """
        pending_backfills = (
            self.db.query(Backfill)
            .filter_by(backtest_id=backtest.backtest_id)
            .filter(Backfill.status.in_(_IN_PROGRESS_RUN_STATUS))
            .all()
        )

        pending_jobs = len(pending_backfills)
        self.logger.debug(
            "[backtest %s] Found %d backfills in progress",
            backtest.backtest_id,
            len(pending_backfills),
        )

        for backfill in pending_backfills:
            self.logger.debug(
                "[backtest %s] Checking backfill %s",
                backtest.backtest_id,
                backfill.backfill_id,
            )
            status = await async_get_backtest_job_status(backfill.gcp_job_id)
            if status in _IN_PROGRESS_RUN_STATUS:
                # Still in progress.
                continue

            # When done, mark status and decrease the pending jobs counter.
            backfill.status = status
            self.db.commit()
            self.logger.debug(
                f"Backfill {backfill.backfill_id} finished with {status=}"
            )
            pending_jobs -= 1

        return pending_jobs

    def _backfills_succeeded(self, backtest: Backtest) -> bool:
        backfills = (
            self.db.query(Backfill)
            .filter_by(backtest_id=backtest.backtest_id, status=RunStatus.FAILURE)
            .all()
        )
        return len(backfills) == 0


_IN_PROGRESS_BACKTEST_STATUS = {JobStatus.RUNNING, JobStatus.PENDING}
_IN_PROGRESS_RUN_STATUS = {RunStatus.PENDING, RunStatus.STARTED}

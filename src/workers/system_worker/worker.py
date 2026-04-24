from arq import cron
from codex_core.common.loguru_setup import setup_logging
from codex_platform.workers.arq import BaseArqWorkerSettings, base_shutdown, base_startup
from loguru import logger as log

from src.workers.core.config import WorkerSettings as CoreWorkerSettings

from .dependencies import SHUTDOWN_DEPENDENCIES, STARTUP_DEPENDENCIES
from .tasks.maintenance import ensure_tasks_scheduled, system_watchdog_task
from .tasks.task_aggregator import FUNCTIONS

settings = CoreWorkerSettings()


async def worker_startup(ctx: dict) -> None:
    setup_logging(settings, "system_worker")
    await base_startup(ctx)

    log.info("SystemWorkerStartup | Initializing dependencies.")
    for dependency_func in STARTUP_DEPENDENCIES:
        await dependency_func(ctx, settings)

    await ensure_tasks_scheduled(ctx)
    log.info("SystemWorkerStartup | All dependencies initialized.")


async def worker_shutdown(ctx: dict) -> None:
    log.info("SystemWorkerShutdown | Shutting down dependencies.")
    for dependency_func in SHUTDOWN_DEPENDENCIES:
        await dependency_func(ctx, settings)
    log.info("SystemWorkerShutdown | All dependencies shut down.")

    await base_shutdown(ctx)


class WorkerSettings(BaseArqWorkerSettings):
    redis_settings = settings.arq_redis_settings
    max_jobs = settings.arq_max_jobs
    # ARQ requires job_timeout to be an integer.
    job_timeout = int(max(settings.arq_job_timeout, settings.internal_api_timeout + 30))
    keep_result = settings.arq_keep_result
    queue_name = "system"

    on_startup = worker_startup
    on_shutdown = worker_shutdown

    functions = FUNCTIONS
    cron_jobs = [
        cron(system_watchdog_task, minute=None, run_at_startup=True),
    ]

from codex_core.common.loguru_setup import setup_logging
from codex_platform.workers.arq import BaseArqWorkerSettings, base_shutdown, base_startup
from loguru import logger as log

from src.workers.core.config import WorkerSettings as CoreWorkerSettings

from .dependencies import SHUTDOWN_DEPENDENCIES, STARTUP_DEPENDENCIES
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


async def ensure_tasks_scheduled(ctx: dict) -> None:
    """Ensures that periodic tasks are enqueued if they aren't already."""
    arq_service = ctx.get("arq_service")
    if not arq_service:
        log.warning("Seeding skipped: arq_service not found in context.")
        return

    # Task mapping: (function_name, task_id)
    tasks = [
        ("import_emails_task", "conversations.import"),
        ("flush_tracking_task", "tracking.flush"),
        ("booking_maintenance_task", "booking.worker"),
    ]

    for func_name, task_id in tasks:
        # ARQ's job_id uniqueness prevents double-enqueuing if already scheduled.
        try:
            job = await arq_service.enqueue_job(
                func_name,
                _job_id=f"{task_id}:next",
                _queue_name="system",
            )
            if job:
                log.info("Seeding task scheduled: {}", task_id)
            else:
                log.debug("Seeding skipped: {} already in queue.", task_id)
        except Exception as exc:
            log.error("Failed to seed task {}: {}", task_id, exc)


async def worker_shutdown(ctx: dict) -> None:
    log.info("SystemWorkerShutdown | Shutting down dependencies.")
    for dependency_func in SHUTDOWN_DEPENDENCIES:
        await dependency_func(ctx, settings)
    log.info("SystemWorkerShutdown | All dependencies shut down.")

    await base_shutdown(ctx)


class WorkerSettings(BaseArqWorkerSettings):
    redis_settings = settings.arq_redis_settings
    max_jobs = settings.arq_max_jobs
    job_timeout = max(settings.arq_job_timeout, settings.internal_api_timeout + 30)
    keep_result = settings.arq_keep_result
    queue_name = "system"

    on_startup = worker_startup
    on_shutdown = worker_shutdown

    functions = FUNCTIONS

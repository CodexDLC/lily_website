from loguru import logger as log


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


async def system_watchdog_task(ctx: dict) -> None:
    """Watchdog task that runs periodically to ensure all other tasks are enqueued."""
    log.info("SystemWatchdog | Action: Checking tasks health.")
    await ensure_tasks_scheduled(ctx)

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

from src.workers.core.heartbeat import HeartbeatTask, WorkerHeartbeatRegistry

if TYPE_CHECKING:
    from src.workers.system_worker.config import WorkerSettings

TASK_ID = "booking.worker"
QUEUE_NAME = "system"


async def booking_maintenance_task(ctx: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Placeholder heartbeat for future booking reminder/reschedule jobs."""

    settings = cast("WorkerSettings", ctx["settings"])
    registry = cast("WorkerHeartbeatRegistry", ctx["heartbeat_registry"])
    task = HeartbeatTask(
        task_id=TASK_ID,
        domain="booking",
        queue_name=QUEUE_NAME,
        expected_interval_sec=settings.booking_worker_interval_sec,
        stale_after_sec=settings.booking_worker_stale_after_sec,
    )
    if not await registry.should_run(task.task_id, lock_ttl_sec=task.stale_after_sec):
        await registry.mark_finished(task, status="skipped")
        return None

    try:
        await registry.mark_started(task, job_id=str(ctx.get("job_id", "")))
        log.info("booking_maintenance_task heartbeat completed; no booking actions configured yet.")
        await _schedule_next(ctx, task)
        await registry.mark_finished(task, status="success")
        return {"status": "ok", "actions": 0}
    except Exception as exc:
        log.exception("booking_maintenance_task failed")
        await registry.mark_finished(task, status="failed", error=str(exc))
        # Ensure we still try to reschedule even if this run failed
        await _schedule_next(ctx, task)
        raise
    finally:
        await registry.release_lock(task.task_id)


async def _schedule_next(ctx: dict[str, Any], task: HeartbeatTask) -> None:
    arq_service = ctx.get("arq_service")
    if not arq_service:
        return
    await arq_service.enqueue_job(
        "booking_maintenance_task",
        _defer_by=timedelta(seconds=task.expected_interval_sec),
        _queue_name=task.queue_name,
        _job_id=f"{task.task_id}:next",
    )

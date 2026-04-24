from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

from src.workers.core.heartbeat import HeartbeatTask, WorkerHeartbeatRegistry

if TYPE_CHECKING:
    from src.workers.core.internal_api import InternalApiClient
    from src.workers.system_worker.config import WorkerSettings

TASK_ID = "tracking.flush"
QUEUE_NAME = "system"


async def flush_tracking_task(ctx: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    settings = cast("WorkerSettings", ctx["settings"])
    registry = cast("WorkerHeartbeatRegistry", ctx["heartbeat_registry"])
    task = HeartbeatTask(
        task_id=TASK_ID,
        domain="tracking",
        queue_name=QUEUE_NAME,
        expected_interval_sec=settings.tracking_flush_interval_sec,
        stale_after_sec=settings.tracking_flush_stale_after_sec,
    )
    if not await registry.should_run(task.task_id, lock_ttl_sec=task.stale_after_sec):
        await registry.mark_finished(task, status="skipped")
        return None

    try:
        await registry.mark_started(task, job_id=str(ctx.get("job_id", "")))
        client = cast("InternalApiClient", ctx["internal_api"])
        result = await client.post(
            "/v1/tracking/flush",
            scope=TASK_ID,
            token=settings.tracking_worker_api_key,
        )
        await _schedule_next(ctx, registry, task)
        await registry.mark_finished(task, status="success")
        return result
    except Exception as exc:
        log.exception("flush_tracking_task failed")
        await registry.mark_finished(task, status="failed", error=str(exc))
        # Ensure we still try to reschedule even if this run failed
        await _schedule_next(ctx, registry, task)
        raise
    finally:
        await registry.release_lock(task.task_id)


async def _schedule_next(ctx: dict[str, Any], registry: WorkerHeartbeatRegistry, task: HeartbeatTask) -> None:
    arq_service = ctx.get("arq_service")
    if not arq_service:
        return
    await arq_service.enqueue_job(
        "flush_tracking_task",
        _defer_by=timedelta(seconds=task.expected_interval_sec),
        _queue_name=task.queue_name,
        _job_id=f"{task.task_id}:next",
    )

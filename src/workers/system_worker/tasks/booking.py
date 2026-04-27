from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

from src.workers.core.heartbeat import HeartbeatTask, WorkerHeartbeatRegistry

if TYPE_CHECKING:
    from src.workers.core.internal_api import InternalApiClient
    from src.workers.system_worker.config import WorkerSettings

TASK_ID = "booking.worker"
QUEUE_NAME = "system"


async def booking_maintenance_task(ctx: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Booking maintenance root task. Runs every 15 min, dispatches notification branches."""

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

    actions = 0
    try:
        await registry.mark_started(task, job_id=str(ctx.get("job_id", "")))
        actions += await _run_reminders_branch(ctx, settings)
        await _schedule_next(ctx, task)
        await registry.mark_finished(task, status="success")
        return {"status": "ok", "actions": actions}
    except Exception as exc:
        log.exception("booking_maintenance_task failed")
        await registry.mark_finished(task, status="failed", error=str(exc))
        await _schedule_next(ctx, task)
        raise
    finally:
        await registry.release_lock(task.task_id)


async def _run_reminders_branch(ctx: dict[str, Any], settings: Any) -> int:
    """Query appointments due for reminders and enqueue send tasks."""
    token = settings.booking_worker_api_key
    if not token:
        log.warning("booking_maintenance_task: BOOKING_WORKER_API_KEY not set, skipping reminders")
        return 0

    api = cast("InternalApiClient", ctx["internal_api"])
    arq = ctx["arq_service"]

    appointments = await api.get(
        "/booking/appointments/reminders-due",
        scope="booking.worker",
        token=token,
    )

    if not isinstance(appointments, list):
        log.warning(f"booking_maintenance_task: unexpected reminders-due response: {appointments}")
        return 0

    queued = 0
    for appt in appointments:
        appt_id = appt.get("id")
        if not appt_id:
            continue

        if not appt.get("client_email"):
            log.warning(f"booking_maintenance_task: appointment {appt_id} has no client email, skipping")
            continue

        job = await arq.enqueue_job(
            "send_booking_reminder_task",
            appt,
            _queue_name="notifications",
            _job_id=f"reminder:{appt_id}",
        )
        if job:
            try:
                await api.post(
                    f"/booking/appointments/{appt_id}/mark-reminder-sent",
                    scope="booking.worker",
                    token=token,
                )
            except Exception as mark_exc:
                log.warning(f"booking_maintenance_task: failed to mark reminder sent for {appt_id}: {mark_exc}")
            queued += 1
            log.info(f"booking_maintenance_task: queued reminder for appointment {appt_id}")
        else:
            log.debug(f"booking_maintenance_task: reminder already queued for appointment {appt_id}")

    log.info(f"booking_maintenance_task: reminders branch done, queued={queued}")
    return queued


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

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from redis.asyncio import Redis


@dataclass(frozen=True)
class HeartbeatTask:
    task_id: str
    domain: str
    queue_name: str
    expected_interval_sec: int
    stale_after_sec: int


class WorkerHeartbeatRegistry:
    """Redis registry for self-scheduling ARQ tasks."""

    prefix = "worker:tasks"

    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client

    async def should_run(self, task_id: str, *, lock_ttl_sec: int) -> bool:
        enabled = await cast("Awaitable[Any]", self.redis_client.hget(self._task_key(task_id), "enabled"))
        if enabled == "0":
            return False
        return bool(await self.redis_client.set(self._lock_key(task_id), "1", ex=lock_ttl_sec, nx=True))

    async def release_lock(self, task_id: str) -> None:
        await self.redis_client.delete(self._lock_key(task_id))

    async def mark_started(self, task: HeartbeatTask, *, job_id: str | None = None) -> None:
        now = _now()
        await cast(
            "Awaitable[Any]",
            self.redis_client.hset(
                self._task_key(task.task_id),
                mapping={
                    "task_id": task.task_id,
                    "domain": task.domain,
                    "queue_name": task.queue_name,
                    "enabled": "1",
                    "expected_interval_sec": str(task.expected_interval_sec),
                    "stale_after_sec": str(task.stale_after_sec),
                    "last_started_at": now,
                    "last_status": "running",
                    "last_job_id": job_id or "",
                },
            ),
        )
        await self._event(task.task_id, {"status": "running", "at": now})

    async def mark_finished(
        self,
        task: HeartbeatTask,
        *,
        status: str,
        next_due_at: datetime | None = None,
        error: str = "",
    ) -> None:
        key = self._task_key(task.task_id)
        now = _now()
        current_failures_raw = await cast("Awaitable[Any]", self.redis_client.hget(key, "consecutive_failures"))
        current_failures = int(current_failures_raw or 0)
        failures = current_failures + 1 if status not in {"success", "skipped"} else 0
        await cast(
            "Awaitable[Any]",
            self.redis_client.hset(
                key,
                mapping={
                    "last_finished_at": now,
                    "next_due_at": next_due_at.isoformat() if next_due_at else "",
                    "last_status": status,
                    "last_error": error[:1000],
                    "consecutive_failures": str(failures),
                },
            ),
        )
        await self._event(task.task_id, {"status": status, "at": now, "error": error[:300]})

    async def schedule_next(self, ctx: dict[str, Any], task: HeartbeatTask, *, function_name: str) -> str | None:
        arq_service = ctx.get("arq_service")
        if not arq_service:
            return None
        defer = timedelta(seconds=task.expected_interval_sec)
        job = await arq_service.enqueue_job(
            function_name,
            _defer_by=defer,
            _queue_name=task.queue_name,
            _job_id=f"{task.task_id}:next",
        )
        next_due = datetime.now(UTC) + defer
        await self.mark_finished(task, status="success", next_due_at=next_due)
        return str(getattr(job, "job_id", "")) if job else None

    async def _event(self, task_id: str, payload: dict[str, Any]) -> None:
        key = f"{self._task_key(task_id)}:events"
        await cast("Awaitable[Any]", self.redis_client.lpush(key, json.dumps(payload, ensure_ascii=False)))
        await cast("Awaitable[Any]", self.redis_client.ltrim(key, 0, 99))

    def _task_key(self, task_id: str) -> str:
        return f"{self.prefix}:{task_id}"

    def _lock_key(self, task_id: str) -> str:
        return f"{self._task_key(task_id)}:lock"


def _now() -> str:
    return datetime.now(UTC).isoformat()

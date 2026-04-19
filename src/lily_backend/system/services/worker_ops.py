from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

from django.conf import settings
from redis import Redis

TASK_FUNCTIONS = {
    "conversations.import": "import_emails_task",
    "tracking.flush": "flush_tracking_task",
    "booking.worker": "booking_maintenance_task",
}

TASK_METADATA: dict[str, dict[str, Any]] = {
    "conversations.import": {"domain": "Conversations", "queue_name": "system", "interval": 60},
    "tracking.flush": {"domain": "Tracking", "queue_name": "system", "interval": 10},
    "booking.worker": {"domain": "Booking", "queue_name": "system", "interval": 300},
}


@dataclass(frozen=True)
class WorkerTaskStatus:
    task_id: str
    domain: str
    queue_name: str
    enabled: bool
    expected_interval_sec: int
    stale_after_sec: int
    last_started_at: str
    last_finished_at: str
    next_due_at: str
    last_status: str
    last_job_id: str
    last_error: str
    consecutive_failures: int
    health: str


class WorkerOpsService:
    prefix = "worker:tasks"

    def __init__(self, redis_client: Redis | None = None) -> None:
        self.redis_url = _redis_url()
        self.redis = redis_client or self._build_redis_client()

    def list_tasks(self) -> list[WorkerTaskStatus]:
        if self.redis is None:
            raise RuntimeError(
                "Redis host 'redis' is only resolvable inside Docker. "
                "For local Cabinet set REDIS_URL/ARQ_REDIS_URL to localhost:6380 or open Ops from the backend container."
            )
        found_keys = sorted(
            cast_key(key)
            for key in self.redis.scan_iter(f"{self.prefix}:*")
            if not str(key).endswith((":events", ":lock"))
        )

        tasks = []
        for key in found_keys:
            task_id = key.removeprefix(f"{self.prefix}:")
            key = f"{self.prefix}:{task_id}"
            data = cast("dict[str, Any]", self.redis.hgetall(key))
            tasks.append(self._task_from_hash(key, data))

        return tasks

    def summary(self) -> dict[str, Any]:
        try:
            tasks = self.list_tasks()
        except Exception as exc:
            return {
                "tasks": [],
                "total": 0,
                "critical": 1,
                "degraded": 0,
                "healthy": 0,
                "status": "critical",
                "error": str(exc),
            }
        critical = [task for task in tasks if task.health == "critical"]
        degraded = [task for task in tasks if task.health == "degraded"]
        return {
            "tasks": tasks,
            "total": len(tasks),
            "critical": len(critical),
            "degraded": len(degraded),
            "healthy": len([task for task in tasks if task.health == "healthy"]),
            "status": "critical" if critical else "degraded" if degraded else "healthy",
            "error": "",
        }

    def set_enabled(self, task_id: str, enabled: bool) -> None:
        if self.redis:
            self.redis.hset(
                f"{self.prefix}:{task_id}", mapping={"task_id": task_id, "enabled": "1" if enabled else "0"}
            )

    def enqueue_now(self, task_id: str, *, defer_by: int | None = None) -> str | None:
        from core.arq.client import arq_client

        function = TASK_FUNCTIONS.get(task_id)
        if not function:
            return None
        return arq_client.enqueue(
            function,
            {},
            queue_name="system",
            defer_by=defer_by,
            job_id=f"{task_id}:manual",
        )

    def _build_redis_client(self) -> Redis | None:
        if _is_docker_only_hostname(self.redis_url):
            return None
        return Redis.from_url(
            self.redis_url,
            decode_responses=True,
            socket_connect_timeout=0.35,
            socket_timeout=0.35,
            retry_on_timeout=False,
            health_check_interval=0,
        )

    def _task_from_hash(self, key: str, data: dict[str, Any]) -> WorkerTaskStatus:
        task_id = str(data.get("task_id") or key.removeprefix(f"{self.prefix}:"))
        stale_after = _int(data.get("stale_after_sec"), 0)
        last_started = str(data.get("last_started_at", ""))
        health = _health(data, stale_after=stale_after)

        # Fallback to metadata for non-started tasks
        meta = TASK_METADATA.get(task_id, {})
        domain = str(data.get("domain") or meta.get("domain", "System"))
        queue_name = str(data.get("queue_name") or meta.get("queue_name", "system"))
        expected_interval = _int(data.get("expected_interval_sec"), meta.get("interval", 0))

        return WorkerTaskStatus(
            task_id=task_id,
            domain=domain,
            queue_name=queue_name,
            enabled=str(data.get("enabled", "1")) != "0",
            expected_interval_sec=expected_interval,
            stale_after_sec=stale_after,
            last_started_at=last_started,
            last_finished_at=str(data.get("last_finished_at", "")),
            next_due_at=str(data.get("next_due_at", "")),
            last_status=str(data.get("last_status", "unknown")),
            last_job_id=str(data.get("last_job_id", "")),
            last_error=str(data.get("last_error", "")),
            consecutive_failures=_int(data.get("consecutive_failures"), 0),
            health=health,
        )


def _health(data: dict[str, Any], *, stale_after: int) -> str:
    if str(data.get("enabled", "1")) == "0":
        return "disabled"
    failures = _int(data.get("consecutive_failures"), 0)
    if failures >= 3:
        return "critical"
    last_status = str(data.get("last_status", ""))
    if last_status == "failed":
        return "degraded"
    last_started = _parse_dt(str(data.get("last_started_at", "")))
    if stale_after and last_started and (datetime.now(UTC) - last_started).total_seconds() > stale_after:
        return "critical"
    if not last_started:
        return "degraded"
    return "healthy"


def _parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _redis_url() -> str:
    return str(getattr(settings, "ARQ_REDIS_URL", None) or getattr(settings, "REDIS_URL", "redis://localhost:6379/0"))


def _is_docker_only_hostname(redis_url: str) -> bool:
    hostname = urlparse(redis_url).hostname
    return hostname == "redis" and not Path("/.dockerenv").exists()


def cast_key(value: Any) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)

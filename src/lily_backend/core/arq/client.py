from __future__ import annotations

import asyncio
from typing import Any

from arq.connections import RedisSettings, create_pool
from asgiref.sync import async_to_sync
from django.conf import settings


class DjangoArqClient:
    """
    Django-facing ARQ client compatible with both local legacy calls and codex_django 0.4+.

    Supported contracts:
    - ``enqueue()/aenqueue()`` for ``codex_django.notifications``
    - ``enqueue_job()`` for direct ARQ usage
    """

    _pool: Any | None = None
    _pool_loop: asyncio.AbstractEventLoop | None = None

    @classmethod
    async def get_pool(cls) -> Any:
        current_loop = asyncio.get_running_loop()
        if cls._pool is None or cls._pool_loop is not current_loop:
            redis_url = str(
                getattr(settings, "ARQ_REDIS_URL", None) or getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
            )
            cls._pool = await create_pool(RedisSettings.from_dsn(redis_url))
            cls._pool_loop = current_loop
        return cls._pool

    @staticmethod
    def _job_id(job: Any) -> str | None:
        if job is None:
            return None
        return str(getattr(job, "job_id", job))

    @classmethod
    async def enqueue_job(cls, function: str, *args: Any, **kwargs: Any) -> Any:
        pool = await cls.get_pool()
        return await pool.enqueue_job(function, *args, **kwargs)

    @classmethod
    async def aenqueue(
        cls,
        task_name: str,
        payload: dict[str, Any] | None = None,
        *,
        queue_name: str | None = None,
        defer_by: Any = None,
        job_id: str | None = None,
    ) -> str | None:
        kwargs: dict[str, Any] = {}
        if payload is not None:
            kwargs["payload"] = payload
        if queue_name:
            kwargs["_queue_name"] = queue_name
        if defer_by is not None:
            kwargs["_defer_by"] = defer_by
        if job_id:
            kwargs["_job_id"] = job_id
        job = await cls.enqueue_job(task_name, **kwargs)
        return cls._job_id(job)

    @classmethod
    def enqueue(
        cls,
        task_name: str,
        payload: dict[str, Any] | None = None,
        *,
        queue_name: str | None = None,
        defer_by: Any = None,
        job_id: str | None = None,
    ) -> str | None:
        kwargs: dict[str, Any] = {}
        if queue_name is not None:
            kwargs["queue_name"] = queue_name
        if defer_by is not None:
            kwargs["defer_by"] = defer_by
        if job_id is not None:
            kwargs["job_id"] = job_id
        return async_to_sync(cls.aenqueue)(task_name, payload, **kwargs)


arq_client = DjangoArqClient

import asyncio
from typing import Any

from arq.connections import ArqRedis, RedisSettings, create_pool
from django.conf import settings


class DjangoArqClient:
    """
    ARQ Client for Django (Producer).
    Allows sending tasks to Redis queue from synchronous Django views.
    """

    _pool: ArqRedis | None = None

    @classmethod
    async def get_pool(cls) -> ArqRedis:
        """
        Returns (or creates) an async Redis pool.
        """
        if cls._pool is None:
            redis_settings = RedisSettings(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                database=0,
            )
            cls._pool = await create_pool(redis_settings)
        return cls._pool

    @classmethod
    async def enqueue_job_async(cls, function: str, *args: Any, **kwargs: Any) -> Any | None:
        """
        Async method to enqueue a job.
        """
        try:
            pool = await cls.get_pool()
            job = await pool.enqueue_job(function, *args, **kwargs)
            return job
        except Exception as e:
            # Log error (using print or logging)
            print(f"ARQ Error: Failed to enqueue job '{function}': {e}")
            return None

    @classmethod
    def enqueue_job(cls, function: str, *args: Any, **kwargs: Any) -> Any | None:
        """
        Synchronous wrapper to enqueue a job from Django views.
        Creates a new event loop if needed.
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                # If closed, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # No event loop exists, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(cls.enqueue_job_async(function, *args, **kwargs))

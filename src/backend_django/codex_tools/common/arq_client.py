"""
codex_tools.common.arq_client
==============================
Универсальный клиент для ARQ (Producer).

Позволяет синхронному коду ставить задачи в асинхронную очередь Redis.
Не зависит от Django settings напрямую.
"""

import asyncio
from typing import Any

from arq.connections import ArqRedis, RedisSettings, create_pool


class BaseArqClient:
    """
    Базовый клиент для работы с очередью ARQ.
    """

    _pool: ArqRedis | None = None

    def __init__(self, redis_host: str, redis_port: int, redis_password: str | None = None):
        self.redis_settings = RedisSettings(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            database=0,
        )

    async def get_pool(self) -> ArqRedis:
        if self._pool is None:
            self._pool = await create_pool(self.redis_settings)
        return self._pool

    async def enqueue_job_async(self, function: str, *args: Any, **kwargs: Any) -> Any:
        try:
            pool = await self.get_pool()
            return await pool.enqueue_job(function, *args, **kwargs)
        except Exception as e:
            # В библиотеке лучше пробрасывать исключение или использовать логгер
            raise e

    def enqueue_job(self, function: str, *args: Any, **kwargs: Any) -> Any:
        """Синхронная обертка для использования в Django views."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.enqueue_job_async(function, *args, **kwargs))

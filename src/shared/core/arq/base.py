from typing import Any

from arq.connections import ArqRedis, RedisSettings, create_pool
from loguru import logger as log

# Предполагаем, что настройки Redis лежат где-то в shared config
# Если нет, нужно будет передавать их явно или импортировать
# Пока сделаем заглушку или импорт из telegram_bot.core.config (но это нарушение слоев)
# Лучше всего, если BaseArqSettings будет абстрактным или принимать настройки

class ArqService:
    """
    Обертка над клиентом ARQ.
    Позволяет создавать пул один раз и переиспользовать его.
    """

    def __init__(self, redis_settings: RedisSettings):
        self.pool: ArqRedis | None = None
        self.redis_settings = redis_settings

    async def init(self):
        """Инициализация пула (вызывать при старте приложения)."""
        if not self.pool:
            try:
                self.pool = await create_pool(self.redis_settings)
                log.debug("ArqService | action=init status=success")
            except Exception as e:
                log.exception(f"ArqService | action=init status=failed error={e}")
                raise

    async def close(self):
        """Закрытие пула (вызывать при остановке приложения)."""
        if self.pool:
            try:
                await self.pool.close()
                log.debug("ArqService | action=close status=success")
            except Exception as e:
                log.exception(f"ArqService | action=close status=failed error={e}")

    async def enqueue_job(self, function: str, *args: Any, **kwargs: Any) -> Any | None:
        """
        Отправка задачи в очередь.
        """
        if not self.pool:
            await self.init()

        if self.pool:
            try:
                job = await self.pool.enqueue_job(function, *args, **kwargs)
                log.debug(f"ArqService | action=enqueue_job function={function} job_id={job.job_id if job else 'None'}")
                return job
            except Exception as e:
                log.exception(f"ArqService | action=enqueue_job status=failed function={function} error={e}")
                return None
        return None


async def base_startup(ctx: dict) -> None:
    """
    Базовая инициализация для всех воркеров.
    """
    log.info("ArqWorkerStartup | status=starting")
    # Здесь можно инициализировать общие ресурсы (Redis, DB)
    # Но так как настройки Redis приходят извне, мы ожидаем их в ctx или конфиге
    log.info("ArqWorkerStartup | status=success")


async def base_shutdown(ctx: dict) -> None:
    """
    Базовая очистка ресурсов.
    """
    log.info("ArqWorkerShutdown | status=starting")
    # Закрытие ресурсов
    log.info("ArqWorkerShutdown | status=success")


class BaseArqSettings:
    """
    Базовые настройки для всех ARQ воркеров.
    Наследники должны переопределить redis_settings и functions.
    """
    max_jobs = 20
    job_timeout = 60
    keep_result = 5

    on_startup = base_startup
    on_shutdown = base_shutdown

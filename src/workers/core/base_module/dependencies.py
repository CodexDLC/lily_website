from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger as log
from redis.asyncio import from_url

from src.shared.core.manager_redis.site_settings_manager import SiteSettingsManager
from src.shared.core.redis_service import RedisService
from src.workers.core.config import WorkerSettings

# Определение типа для функций-зависимостей
DependencyFunction = Callable[[dict[str, Any], Any], Awaitable[None]]


async def init_common_dependencies(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """
    Базовая инициализация зависимостей для всех воркеров.
    """
    log.info("Initializing common worker dependencies...")
    try:
        # Сохраняем настройки в контекст, чтобы задачи могли их достать
        ctx["settings"] = settings

        # 1. Создаем клиент Redis
        redis_client = from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        ctx["redis_client"] = redis_client

        # 2. Инициализируем RedisService
        redis_service = RedisService(redis_client)
        ctx["redis_service"] = redis_service

        # 3. Инициализируем SiteSettingsManager и загружаем настройки
        site_settings_manager = SiteSettingsManager(redis_service, settings)
        site_settings_obj = await site_settings_manager.get_settings_obj()

        ctx["site_settings"] = site_settings_obj
        log.info("Common worker dependencies initialized successfully.")

    except Exception as e:
        log.exception(f"Failed to initialize common worker dependencies: {e}")
        raise


async def close_common_dependencies(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """
    Очистка общих ресурсов.
    """
    log.info("Closing common worker dependencies...")
    redis_client = ctx.get("redis_client")
    if redis_client:
        await redis_client.close()
        log.info("Redis connection closed.")

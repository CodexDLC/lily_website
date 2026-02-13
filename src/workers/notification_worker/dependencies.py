from collections.abc import Awaitable, Callable

from loguru import logger as log
from redis.asyncio import from_url

from src.shared.core.redis_service import RedisService
from src.shared.core.stream.manager import StreamManager
from src.workers.core.config import WorkerSettings

# Определяем тип для функций инициализации/очистки зависимостей
DependencyFunction = Callable[[dict, WorkerSettings], Awaitable[None]]


async def init_redis_stream_manager(ctx: dict, settings: WorkerSettings) -> None:
    """
    Инициализация RedisService и StreamManager для работы со стримами.
    """
    log.info("Initializing Redis Stream Manager...")
    try:
        # Создаем клиент Redis
        redis_client = from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

        # Инициализируем сервисы
        redis_service = RedisService(redis_client)
        stream_manager = StreamManager(redis_service)

        # Сохраняем в контекст
        ctx["redis_client"] = redis_client
        ctx["stream_manager"] = stream_manager

        log.info("Redis Stream Manager initialized successfully.")
    except Exception as e:
        log.exception(f"Failed to initialize Redis Stream Manager: {e}")
        raise


async def close_redis_stream_manager(ctx: dict, settings: WorkerSettings) -> None:
    """
    Закрытие соединения с Redis.
    """
    log.info("Closing Redis Stream Manager...")
    redis_client = ctx.get("redis_client")
    if redis_client:
        await redis_client.close()
        log.info("Redis connection closed.")


# Список функций, которые будут выполняться при старте воркера
STARTUP_DEPENDENCIES: list[DependencyFunction] = [
    init_redis_stream_manager,
]

# Список функций, которые будут выполняться при остановке воркера
SHUTDOWN_DEPENDENCIES: list[DependencyFunction] = [
    close_redis_stream_manager,
]

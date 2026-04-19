from collections.abc import Awaitable, Callable
from typing import Any

from codex_platform.redis_service import RedisService
from loguru import logger as log
from redis.asyncio import from_url

from src.workers.core.config import WorkerSettings
from src.workers.core.heartbeat import WorkerHeartbeatRegistry
from src.workers.core.internal_api import InternalApiClient
from src.workers.core.site_settings import SiteSettingsRedisReader, merge_email_settings
from src.workers.core.streams import StreamManager

DependencyFunction = Callable[[dict[str, Any], Any], Awaitable[None]]


async def init_common_dependencies(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """Initialize worker-shared Redis, SiteSettings, streams and API client."""

    log.info("Initializing common worker dependencies...")
    redis_client = from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    ctx["settings"] = settings
    ctx["redis_client"] = redis_client
    ctx["redis_service"] = RedisService(redis_client)
    ctx["stream_manager"] = StreamManager(redis_client)
    ctx["heartbeat_registry"] = WorkerHeartbeatRegistry(redis_client)

    reader = SiteSettingsRedisReader(
        redis_client,
        project_namespace=settings.redis_site_settings_project,
        base_key=settings.redis_site_settings_key,
    )
    ctx["site_settings"] = merge_email_settings(await reader.load(), settings)

    internal_api = InternalApiClient(
        base_url=settings.backend_api_base_url,
        timeout=settings.internal_api_timeout,
    )
    await internal_api.open()
    ctx["internal_api"] = internal_api
    log.info("Common worker dependencies initialized successfully.")


async def close_common_dependencies(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """Close worker-shared resources."""

    log.info("Closing common worker dependencies...")
    internal_api = ctx.get("internal_api")
    if internal_api:
        await internal_api.close()
    redis_client = ctx.get("redis_client")
    if redis_client:
        await redis_client.close()
        log.info("Redis connection closed.")

from typing import Any

from codex_platform.workers.arq import BaseArqService
from loguru import logger as log

from src.workers.core.base_module.dependencies import (
    DependencyFunction,
    close_common_dependencies,
    init_common_dependencies,
)
from src.workers.system_worker.config import WorkerSettings


async def init_arq_service(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    arq_service = BaseArqService(settings.arq_redis_settings)
    await arq_service.init()
    ctx["arq_service"] = arq_service
    log.info("System worker ARQ service initialized.")


async def close_arq_service(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    arq_service = ctx.get("arq_service")
    if arq_service:
        await arq_service.close()


STARTUP_DEPENDENCIES: list[DependencyFunction] = [
    init_common_dependencies,
    init_arq_service,
]

SHUTDOWN_DEPENDENCIES: list[DependencyFunction] = [
    close_arq_service,
    close_common_dependencies,
]

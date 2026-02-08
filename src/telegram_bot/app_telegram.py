"""
Entry point для Telegram Bot.
Подключается к Backend через HTTP API.
"""

import asyncio

from loguru import logger as log
from redis.asyncio import Redis

from src.shared.core.logger import setup_logging
from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.core.container import BotContainer
from src.telegram_bot.core.factory import build_bot
from src.telegram_bot.core.routers import build_main_router
from src.telegram_bot.middlewares.container import ContainerMiddleware
from src.telegram_bot.middlewares.security import SecurityMiddleware
from src.telegram_bot.middlewares.throttling import ThrottlingMiddleware
from src.telegram_bot.middlewares.user_validation import UserValidationMiddleware


async def startup(settings: BotSettings) -> None:
    """Инициализация логирования при запуске бота."""
    setup_logging(settings, service_name="telegram_bot")
    log.info("Telegram Bot starting...")
    log.info(f"Backend API: {settings.backend_api_url}")


async def shutdown(container: BotContainer) -> None:
    """Очистка ресурсов при остановке бота."""
    log.info("Shutting down Telegram Bot...")
    await container.shutdown()
    log.info("Bot stopped")


async def main() -> None:
    """Основная функция запуска Telegram Bot."""
    # 1. Загрузка настроек
    settings = BotSettings()  # type: ignore[call-arg]

    # 2. Логирование
    await startup(settings)

    # 3. Redis
    redis_client = Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    log.debug("Redis client initialized")

    # 4. DI Container
    container = BotContainer(settings, redis_client)
    log.debug("BotContainer initialized")

    # 5. Bot + Dispatcher
    bot, dp = await build_bot(settings.bot_token, redis_client)
    log.info("Bot and Dispatcher created")

    # 6. Middleware (порядок: снаружи → внутрь)
    dp.update.middleware(UserValidationMiddleware())
    dp.update.middleware(ThrottlingMiddleware(redis=redis_client, rate_limit=1.0))
    dp.update.middleware(SecurityMiddleware())
    dp.update.middleware(ContainerMiddleware(container=container))
    log.info("Middleware attached")

    # 7. Роутеры (автоподключение из INSTALLED_FEATURES)
    main_router = build_main_router()
    dp.include_router(main_router)
    log.info("Routers attached")

    # 8. Polling
    log.info("Bot polling started")
    try:
        await dp.start_polling(bot)
    finally:
        await shutdown(container)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot stopped by user")
    except Exception as e:  # noqa: BLE001
        log.critical(f"Critical error: {e}", exc_info=True)

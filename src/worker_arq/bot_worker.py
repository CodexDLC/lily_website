from aiogram import Bot
from arq.connections import RedisSettings
from loguru import logger as log

from src.shared.core.arq.base import BaseArqSettings, base_shutdown, base_startup
from src.telegram_bot.core.config import BotSettings

settings = BotSettings()  # type: ignore[call-arg]
from src.worker_arq.tasks import (  # noqa: E402
    send_booking_notification_task,
    send_notification_task,
)


async def bot_startup(ctx: dict) -> None:
    """
    Инициализация воркера бота.
    Создает экземпляр бота и кладет его в контекст.
    """
    await base_startup(ctx)

    log.info("BotWorkerStartup | initializing bot instance")
    # Создаем бота (важно: используем тот же токен)
    # В реальном проекте лучше передавать уже созданный инстанс или создавать новый
    # Но для воркера нужен свой инстанс, так как это отдельный процесс
    bot = Bot(token=settings.bot_token)
    ctx["bot"] = bot
    log.info("BotWorkerStartup | bot initialized")


async def bot_shutdown(ctx: dict) -> None:
    """
    Очистка ресурсов воркера бота.
    """
    bot = ctx.get("bot")
    if bot:
        await bot.session.close()

    await base_shutdown(ctx)


class BotArqSettings(BaseArqSettings):
    """
    Настройки ARQ воркера для Telegram бота.
    """

    redis_settings = RedisSettings(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        database=0,
    )

    on_startup = bot_startup
    on_shutdown = bot_shutdown

    # Регистрация задач
    functions = [
        send_notification_task,
        send_booking_notification_task,
    ]

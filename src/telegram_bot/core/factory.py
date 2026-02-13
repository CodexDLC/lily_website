from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from loguru import logger as log
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from src.telegram_bot.core.config import BotSettings


async def build_bot(settings: BotSettings, redis_client: Redis) -> tuple[Bot, Dispatcher]:
    """
    Создает и конфигурирует экземпляры Bot и Dispatcher.
    БЕЗ доступа к БД (DbSessionMiddleware удален).
    """
    log.info("BotFactory | status=started")

    if not settings.bot_token:
        log.critical("BotFactory | status=failed reason='BOT_TOKEN not found'")
        raise RuntimeError("BOT_TOKEN не найден.")

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    log.debug("BotFactory | component=Bot status=created")

    log.debug("RedisCheck | status=started")
    try:
        pong = await redis_client.ping()
        if not pong:
            raise RedisConnectionError("Redis ping failed")
        log.info("RedisCheck | status=success")
    except RedisConnectionError as e:
        log.critical(f"RedisCheck | status=failed error='{e}'", exc_info=True)
        raise RuntimeError("Критическая ошибка: не удалось подключиться к Redis.") from e

    storage = RedisStorage(redis=redis_client)
    log.debug("BotFactory | component=RedisStorage status=created")

    dp = Dispatcher(storage=storage, settings=settings)
    log.debug("BotFactory | component=Dispatcher status=created")

    log.info("BotFactory | status=finished")
    return bot, dp

from typing import Any

from aiogram import Bot
from loguru import logger as log
from redis.asyncio import Redis

from src.shared.redis_streams.stream_processor import RedisStreamProcessor
from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.core.settings import (
    REDIS_CONSUMER_GROUP_NAME,
    REDIS_CONSUMER_NAME,
    REDIS_STREAM_NAME,
    REDIS_URL,
)
from src.telegram_bot.features.bot_menu.logic.orchestrator import BotMenuOrchestrator
from src.telegram_bot.features.commands.client import AuthClient
from src.telegram_bot.services.feature_discovery.service import FeatureDiscoveryService
from src.telegram_bot.services.redis_dispatcher import bot_redis_dispatcher  # Импортируем глобальный экземпляр


class BotContainer:
    """
    DI Container for Telegram Bot.
    Содержит настройки, Redis и клиенты к бэкенду.
    Контракты фич получают реализации отсюда.
    """

    def __init__(self, settings: BotSettings, redis_client: Redis):
        self.settings = settings
        self.redis_client = redis_client
        self.bot: Bot | None = None
        # self.bot_redis_dispatcher: Optional[BotRedisDispatcher] = None # Удаляем атрибут

        # --- API Clients (Gateways to Backend) ---
        self.auth_client = AuthClient(
            base_url=settings.backend_api_url,
            api_key=settings.backend_api_key,
            timeout=settings.backend_api_timeout,
        )

        # --- Services ---
        self.discovery_service = FeatureDiscoveryService()

        # Запускаем авто-обнаружение фич (Меню, GC, Роуты)
        self.discovery_service.discover_all()

        # --- Feature Orchestrators ---
        # Словарь {feature_key: orchestrator} — используется Director и handlers
        self.features: dict[str, Any] = {}

        # Создаём оркестраторы из feature_setting.py каждой фичи
        self.features = self.discovery_service.create_feature_orchestrators(self)

        # --- Core Features ---
        # bot_menu — особый случай: создаётся вручную, т.ч. зависит от discovery_service
        self.bot_menu = BotMenuOrchestrator(
            discovery_provider=self.discovery_service,
            settings=self.settings,
        )
        self.features["bot_menu"] = self.bot_menu

        # --- Redis Stream Processor ---
        self.stream_processor = RedisStreamProcessor(
            redis_url=REDIS_URL,
            stream_name=REDIS_STREAM_NAME,
            consumer_group_name=REDIS_CONSUMER_GROUP_NAME,
            consumer_name=REDIS_CONSUMER_NAME,
        )
        # self.stream_processor.set_message_callback(self.bot_redis_dispatcher.process_message) # Этот вызов будет перемещен в set_bot

        log.info(f"BotContainer | initialized features={list(self.features.keys())}")

    def set_bot(self, bot: Bot) -> None:
        """Устанавливает объект Bot в контейнер и инициализирует BotRedisDispatcher."""
        self.bot = bot
        # self.bot_redis_dispatcher = BotRedisDispatcher(bot=self.bot) # Удаляем инициализацию здесь
        bot_redis_dispatcher.set_bot(self.bot)  # Устанавливаем bot в глобальный диспетчер
        self.stream_processor.set_message_callback(bot_redis_dispatcher.process_message)  # Регистрируем колбэк
        log.debug("Bot object set and BotRedisDispatcher initialized in BotContainer.")

    async def shutdown(self):
        """Закрытие соединений при остановке бота."""
        if self.redis_client:
            await self.redis_client.close()
        if self.stream_processor:
            await self.stream_processor.stop_listening()

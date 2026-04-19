import socket
from typing import Any, cast

from aiogram import Bot
from arq import ArqRedis, create_pool
from arq.connections import RedisSettings
from codex_bot.engine.container import BaseBotContainer
from codex_platform.redis_service import SiteSettingsManager
from loguru import logger as log
from redis.asyncio import Redis

from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.features.telegram.bot_menu.logic.orchestrator import BotMenuOrchestrator
from src.telegram_bot.infrastructure.redis.container import RedisContainer
from src.telegram_bot.resources.constants import RedisStreams
from src.telegram_bot.services.feature_discovery.service import FeatureDiscoveryService
from src.telegram_bot.services.redis.dispatcher import bot_redis_dispatcher
from src.telegram_bot.services.redis.stream_processor import RedisStreamProcessor


class BotContainer(BaseBotContainer):
    """
    DI Container for Telegram Bot.
    Содержит настройки, Redis и клиенты к бэкенду.
    Контракты фич получают реализации отсюда.
    """

    def __init__(self, settings: BotSettings, redis_client: Redis):
        super().__init__(settings, redis_client=redis_client)
        self.arq_pool: ArqRedis | None = None

        # --- Redis Layer (Bot Specific) ---
        self.redis = RedisContainer(redis_client)

        # --- Base Services (Shared) ---
        from src.telegram_bot.services.url_signer.service import UrlSignerService

        self.site_settings = SiteSettingsManager(redis_client)
        self.url_signer = UrlSignerService(cast("BotSettings", self.settings))

        # --- Redis Stream Processor (Worker) ---
        consumer_name = f"{RedisStreams.BotEvents.CONSUMER_PREFIX}{socket.gethostname()}"
        self.stream_processor = RedisStreamProcessor(
            redis_client=redis_client,
            stream_name=RedisStreams.BotEvents.NAME,
            consumer_group_name=RedisStreams.BotEvents.GROUP,
            consumer_name=consumer_name,
        )

        # --- Services ---
        self.discovery_service = FeatureDiscoveryService()
        self.discovery_service.discover_all()

        # --- Feature Orchestrators ---
        self.features: dict[str, Any] = {}

        discovered_orchestrators = self.discovery_service.create_feature_orchestrators(self)
        for key, instance in discovered_orchestrators.items():
            self.features[key] = instance
            setattr(self, key, instance)

        # --- Core Features ---
        self.bot_menu = BotMenuOrchestrator(
            discovery_provider=self.discovery_service,
            settings=cast("BotSettings", self.settings),
        )
        self.features["bot_menu"] = self.bot_menu

        log.info(f"BotContainer | initialized features={list(self.features.keys())}")

    async def init_arq(self) -> None:
        settings = cast("BotSettings", self.settings)
        self.arq_pool = await create_pool(
            RedisSettings(
                host=settings.effective_redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                database=0,
            )
        )
        log.info("BotContainer | ARQ pool initialized.")

    def set_bot(self, bot: Bot) -> None:
        super().set_bot(bot)

        bot_redis_dispatcher.set_bot(bot)
        bot_redis_dispatcher.set_container(self)
        self.stream_processor.set_message_callback(bot_redis_dispatcher.process_message)

        log.debug("Bot object set and BotRedisDispatcher initialized in BotContainer.")

    async def shutdown(self) -> None:
        await super().shutdown()
        if self.stream_processor:
            await self.stream_processor.stop_listening()
        if self.arq_pool:
            await self.arq_pool.close()
        if self.redis_client:
            await self.redis_client.close()

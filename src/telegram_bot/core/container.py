import importlib
import socket
from typing import Any, cast

from aiogram import Bot
from arq import ArqRedis, create_pool
from arq.connections import RedisSettings
from codex_bot.engine.container import BaseBotContainer
from codex_bot.engine.discovery import FeatureDiscoveryService
from codex_bot.redis import BotRedisDispatcher, RedisRouter, RedisStreamProcessor
from codex_bot.url_signer import UrlSignerService
from codex_platform.redis_service import SiteSettingsManager
from loguru import logger as log
from redis.asyncio import Redis

from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.core.settings import INSTALLED_FEATURES, INSTALLED_REDIS_FEATURES
from src.telegram_bot.features.telegram.bot_menu.logic.orchestrator import BotMenuOrchestrator
from src.telegram_bot.infrastructure.redis.container import RedisContainer
from src.telegram_bot.infrastructure.redis.stream_storage import CodexPlatformStreamStorage
from src.telegram_bot.resources.constants import RedisStreams


def _feature_names(feature_paths: list[str], feature_type: str) -> list[str]:
    prefix = f"features.{feature_type}."
    return [path.removeprefix(prefix) for path in feature_paths]


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
        self.site_settings = SiteSettingsManager(redis_client)
        self.url_signer = UrlSignerService(cast("BotSettings", self.settings).secret_key)
        self.redis_dispatcher = BotRedisDispatcher()

        # --- Redis Stream Processor (Worker) ---
        consumer_name = f"{RedisStreams.BotEvents.CONSUMER_PREFIX}{socket.gethostname()}"
        stream_storage = CodexPlatformStreamStorage(
            redis_client=redis_client,
            stream_name=RedisStreams.BotEvents.NAME,
            consumer_group_name=RedisStreams.BotEvents.GROUP,
            consumer_name=consumer_name,
        )
        self.stream_processor = RedisStreamProcessor(
            storage=stream_storage,
            stream_name=RedisStreams.BotEvents.NAME,
            consumer_group_name=RedisStreams.BotEvents.GROUP,
            consumer_name=consumer_name,
        )

        # --- Services ---
        self.discovery_service = FeatureDiscoveryService(
            module_prefix="src.telegram_bot.features",
            installed_features=_feature_names(INSTALLED_FEATURES, "telegram"),
            installed_redis_features=_feature_names(INSTALLED_REDIS_FEATURES, "redis"),
        )
        self.discovery_service.discover_all()
        self._include_redis_routers()

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

    def set_bot(self, bot: Bot, i18n_middleware: Any | None = None) -> None:
        super().set_bot(bot)
        self.i18n = i18n_middleware

        self.redis_dispatcher.setup(self)
        self.stream_processor.set_message_callback(self.process_redis_message)

        log.debug("Bot object set and BotRedisDispatcher initialized in BotContainer.")

    async def process_redis_message(self, message: dict[str, Any]) -> None:
        """
        Wraps redis message processing with I18nContext.
        """
        if self.i18n:
            async with self.i18n.context():
                await self.redis_dispatcher.process_message(message)
        else:
            await self.redis_dispatcher.process_message(message)

    def _include_redis_routers(self) -> None:
        for feature_path in INSTALLED_REDIS_FEATURES:
            module_path = f"src.telegram_bot.{feature_path}.handlers"
            try:
                module = importlib.import_module(module_path)
            except ImportError:
                log.debug(f"BotContainer | redis feature='{feature_path}' status=no_handlers")
                continue

            redis_router = getattr(module, "redis_router", None)
            if isinstance(redis_router, RedisRouter):
                self.redis_dispatcher.include_router(redis_router)
                log.info(f"BotContainer | redis feature='{feature_path}' status=loaded")

    async def shutdown(self) -> None:
        await super().shutdown()
        if self.stream_processor:
            await self.stream_processor.stop_listening()
        if self.arq_pool:
            await self.arq_pool.close()
        if self.redis_client:
            await self.redis_client.close()

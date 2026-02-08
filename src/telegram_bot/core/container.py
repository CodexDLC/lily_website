from typing import Any

from loguru import logger as log
from redis.asyncio import Redis

from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.features.commands.client import AuthClient
from src.telegram_bot.features.bot_menu.logic.orchestrator import BotMenuOrchestrator
from src.telegram_bot.services.feature_discovery.service import FeatureDiscoveryService


class BotContainer:
    """
    DI Container for Telegram Bot.
    Содержит настройки, Redis и клиенты к бэкенду.
    Контракты фич получают реализации отсюда.
    """

    def __init__(self, settings: BotSettings, redis_client: Redis):
        self.settings = settings
        self.redis_client = redis_client

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
        # bot_menu — особый случай: создаётся вручную, т.к. зависит от discovery_service
        self.bot_menu = BotMenuOrchestrator(
            discovery_provider=self.discovery_service,
            settings=self.settings,
        )
        self.features["bot_menu"] = self.bot_menu

        log.info(f"BotContainer | initialized features={list(self.features.keys())}")

    async def shutdown(self):
        """Закрытие соединений при остановке бота."""
        if self.redis_client:
            await self.redis_client.close()

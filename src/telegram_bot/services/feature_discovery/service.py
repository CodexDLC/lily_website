import importlib
from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

from src.telegram_bot.core.garbage_collector import GarbageStateRegistry
from src.telegram_bot.core.settings import INSTALLED_FEATURES, INSTALLED_REDIS_FEATURES
from src.telegram_bot.services.redis.dispatcher import bot_redis_dispatcher
from src.telegram_bot.services.redis.router import RedisRouter

if TYPE_CHECKING:
    from src.telegram_bot.core.container import BotContainer


class FeatureDiscoveryService:
    """
    Сервис для автоматического обнаружения конфигураций фич.
    Разделяет фичи на UI (telegram) и Redis (background).
    Поддерживает одинаковые имена фич, добавляя префикс 'redis_' для фоновых задач.
    """

    def __init__(self) -> None:
        self._loaded_features: set[str] = set()

    def discover_all(self) -> None:
        """Запускает полный цикл обнаружения."""
        for feature_path in INSTALLED_FEATURES:
            self._discover_menu(feature_path)
            self._discover_garbage_states(feature_path)

        for feature_path in INSTALLED_REDIS_FEATURES:
            self._discover_redis_handlers(feature_path)
            self._discover_garbage_states(feature_path)

    def create_feature_orchestrators(self, container: "BotContainer") -> dict[str, Any]:
        """
        Создаёт оркестраторы для всех фич.
        Если фича из списка Redis, к её ключу добавляется префикс 'redis_'.
        """
        orchestrators: dict[str, Any] = {}

        # Обрабатываем оба списка
        configs = [(INSTALLED_FEATURES, ""), (INSTALLED_REDIS_FEATURES, "redis_")]

        for feature_list, prefix in configs:
            for feature_path in feature_list:
                module = self._load_feature_setting(feature_path)
                if not module:
                    continue

                factory = getattr(module, "create_orchestrator", None)
                if not factory:
                    continue

                # Базовое имя (последняя часть пути)
                base_name = feature_path.split(".")[-1]

                # Итоговый ключ для контейнера (напр. 'notifications' или 'redis_notifications')
                key = f"{prefix}{base_name}"

                try:
                    orchestrator = factory(container)
                    orchestrators[key] = orchestrator
                    log.debug(f"FeatureDiscovery | orchestrator_created key='{key}' feature='{feature_path}'")
                except Exception as e:
                    log.error(f"FeatureDiscovery | orchestrator_error feature='{feature_path}' error='{e}'")

        return orchestrators

    def get_menu_buttons(self) -> dict[str, dict[str, Any]]:
        """Возвращает кнопки меню только из UI фич."""
        buttons: dict[str, dict[str, Any]] = {}
        for feature_path in INSTALLED_FEATURES:
            btn = self._discover_menu(feature_path)
            if btn:
                key = btn.get("key", feature_path)
                buttons[key] = btn
        return buttons

    def _load_feature_setting(self, feature_path: str) -> Any | None:
        candidates = [
            f"src.telegram_bot.{feature_path}.feature_setting",
            f"src.telegram_bot.{feature_path}",
        ]
        for path in candidates:
            try:
                return importlib.import_module(path)
            except ImportError:
                continue
        return None

    def _discover_menu(self, feature_path: str) -> dict[str, Any] | None:
        module_path = f"src.telegram_bot.{feature_path}.menu"
        try:
            module = importlib.import_module(module_path)
            config = getattr(module, "MENU_CONFIG", None)
            if config and isinstance(config, dict):
                return cast("dict[str, Any]", config)
        except ImportError:
            pass
        return None

    def _discover_garbage_states(self, feature_path: str) -> None:
        module = self._load_feature_setting(feature_path)
        if not module:
            return
        garbage_states = getattr(module, "GARBAGE_STATES", None)
        if garbage_states:
            GarbageStateRegistry.register(garbage_states)
            return
        collect_flag = getattr(module, "GARBAGE_COLLECT", False)
        if collect_flag:
            states = getattr(module, "STATES", None)
            if states:
                GarbageStateRegistry.register(states)

    def _discover_redis_handlers(self, feature_path: str) -> None:
        """Ищет и подключает Redis Stream роутеры."""
        module_path = f"src.telegram_bot.{feature_path}.handlers"
        try:
            module = importlib.import_module(module_path)
            redis_router = getattr(module, "redis_router", None)
            if redis_router and isinstance(redis_router, RedisRouter):
                bot_redis_dispatcher.include_router(redis_router)
                log.info(f"FeatureDiscovery | Redis Stream router connected for feature='{feature_path}'")
        except ImportError:
            pass
        except Exception as e:
            log.error(f"FeatureDiscovery | Redis Stream handlers error for feature='{feature_path}': {e}")

import importlib
from typing import TYPE_CHECKING, Any

from loguru import logger as log

from src.telegram_bot.core.settings import INSTALLED_FEATURES
from src.telegram_bot.core.garbage_collector import GarbageStateRegistry

if TYPE_CHECKING:
    from src.telegram_bot.core.container import BotContainer


class FeatureDiscoveryService:
    """
    Сервис для автоматического обнаружения конфигураций фич.
    Сканирует INSTALLED_FEATURES и ищет:
    1. Конфигурацию меню (menu.py -> MENU_CONFIG)
    2. Настройки Garbage Collector (feature_setting.py -> GARBAGE_COLLECT / STATES)
    3. Фабрики оркестраторов (feature_setting.py -> create_orchestrator)
    """

    def __init__(self):
        self._loaded_features: set[str] = set()

    def discover_all(self):
        """
        Запускает полный цикл обнаружения.
        Обычно вызывается при старте бота.
        """
        for feature_path in INSTALLED_FEATURES:
            self._discover_menu(feature_path)
            self._discover_garbage_states(feature_path)

    def create_feature_orchestrators(self, container: "BotContainer") -> dict[str, Any]:
        """
        Создаёт оркестраторы для всех фич, у которых есть create_orchestrator() в feature_setting.py.
        Возвращает словарь {feature_key: orchestrator_instance}.
        """
        orchestrators: dict[str, Any] = {}

        for feature_path in INSTALLED_FEATURES:
            module = self._load_feature_setting(feature_path)
            if not module:
                continue

            factory = getattr(module, "create_orchestrator", None)
            if not factory:
                continue

            # Определяем ключ: из MENU_CONFIG или из имени фичи
            menu_config = getattr(module, "MENU_CONFIG", None)
            if menu_config and isinstance(menu_config, dict):
                key = menu_config.get("key", feature_path.split(".")[-1])
            else:
                key = feature_path.split(".")[-1]

            try:
                orchestrator = factory(container)
                orchestrators[key] = orchestrator
                log.debug(f"FeatureDiscovery | orchestrator_created key='{key}' feature='{feature_path}'")
            except Exception as e:
                log.error(f"FeatureDiscovery | orchestrator_error feature='{feature_path}' error='{e}'")

        return orchestrators

    def get_menu_buttons(self) -> dict[str, dict]:
        """
        Возвращает собранные кнопки меню.
        """
        buttons = {}
        for feature_path in INSTALLED_FEATURES:
            btn = self._discover_menu(feature_path)
            if btn:
                key = btn.get("key", feature_path)
                buttons[key] = btn
        return buttons

    def _load_feature_setting(self, feature_path: str):
        """
        Загружает модуль feature_setting.py для фичи.
        Пробует: feature_setting.py → __init__.py
        """
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

    def _discover_menu(self, feature_path: str) -> dict | None:
        """Ищет MENU_CONFIG в menu.py"""
        module_path = f"src.telegram_bot.{feature_path}.menu"
        try:
            module = importlib.import_module(module_path)
            config = getattr(module, "MENU_CONFIG", None)
            if config and isinstance(config, dict):
                return config
        except ImportError:
            pass
        except Exception as e:
            log.error(f"FeatureDiscovery | menu_error feature='{feature_path}' error='{e}'")
        return None

    def _discover_garbage_states(self, feature_path: str):
        """
        Ищет настройки GC в feature_setting.py (или __init__.py).
        Ожидает:
        - GARBAGE_COLLECT = True (тогда ищет STATES)
        - GARBAGE_STATES = [...] (явный список)
        """
        module = self._load_feature_setting(feature_path)

        if not module:
            return

        # 1. Явный список
        garbage_states = getattr(module, "GARBAGE_STATES", None)
        if garbage_states:
            GarbageStateRegistry.register(garbage_states)
            log.debug(f"FeatureDiscovery | gc_registered explicit feature='{feature_path}'")
            return

        # 2. Флаг + STATES
        collect_flag = getattr(module, "GARBAGE_COLLECT", False)
        if collect_flag:
            states = getattr(module, "STATES", None)
            if states:
                GarbageStateRegistry.register(states)
                log.debug(f"FeatureDiscovery | gc_registered auto feature='{feature_path}'")
            else:
                log.warning(f"FeatureDiscovery | gc_warning feature='{feature_path}' GARBAGE_COLLECT=True but no STATES found")

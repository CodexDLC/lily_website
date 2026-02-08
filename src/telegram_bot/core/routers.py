"""
Централизованный реестр роутеров для Telegram Bot.
Автоматически подключает фичи из INSTALLED_FEATURES (core/settings.py).
"""

import importlib

from aiogram import Router
from loguru import logger as log

from src.telegram_bot.core.settings import INSTALLED_FEATURES
from src.telegram_bot.services.fsm.common_fsm_handlers import router as common_fsm_router


def collect_feature_routers() -> list[Router]:
    """
    Читает INSTALLED_FEATURES и импортирует router из каждой фичи.
    Ожидает что каждая фича экспортирует `router` из handlers/__init__.py.
    """
    routers: list[Router] = []

    for feature_path in INSTALLED_FEATURES:
        module_path = f"src.telegram_bot.{feature_path}.handlers"
        try:
            module = importlib.import_module(module_path)
            feature_router = getattr(module, "router", None)
            if feature_router and isinstance(feature_router, Router):
                routers.append(feature_router)
                log.info(f"RouterCollector | feature='{feature_path}' status=loaded")
            else:
                log.warning(f"RouterCollector | feature='{feature_path}' status=no_router")
        except ImportError as e:
            log.error(f"RouterCollector | feature='{feature_path}' status=import_error error='{e}'")

    return routers


def build_main_router() -> Router:
    """
    Собирает главный роутер приложения.
    Порядок: фичи из INSTALLED_FEATURES, затем garbage collector (последний).
    """
    main_router = Router(name="main_router")

    feature_routers = collect_feature_routers()
    main_router.include_routers(
        *feature_routers,
        common_fsm_router,  # Garbage collector — всегда последний
    )

    log.info(f"MainRouter | features_loaded={len(feature_routers)}")
    return main_router

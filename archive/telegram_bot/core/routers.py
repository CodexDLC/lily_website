"""
Централизованный реестр роутеров для Telegram Bot.
"""

import importlib

from aiogram import Router
from codex_bot.fsm.common_fsm_handlers import common_fsm_router
from loguru import logger as log

from src.telegram_bot.core.settings import INSTALLED_FEATURES, INSTALLED_REDIS_FEATURES


def collect_feature_routers() -> list[Router]:
    """
    Сканирует фичи на наличие Aiogram роутеров.
    """
    routers: list[Router] = []

    for feature_path in [*INSTALLED_FEATURES, *INSTALLED_REDIS_FEATURES]:
        module_path = f"src.telegram_bot.{feature_path}.handlers"
        try:
            module = importlib.import_module(module_path)
            feature_router = getattr(module, "router", None)
            if feature_router and isinstance(feature_router, Router):
                routers.append(feature_router)
                log.info(f"RouterCollector | feature='{feature_path}' status=loaded")
        except ImportError:
            log.debug(f"RouterCollector | feature='{feature_path}' status=no_handlers")
        except Exception as e:
            log.error(f"RouterCollector | feature='{feature_path}' error='{e}'")

    return routers


def build_main_router() -> Router:
    """Собирает главный роутер приложения."""
    main_router = Router(name="main_router")
    feature_routers = collect_feature_routers()
    main_router.include_routers(*feature_routers, common_fsm_router)
    log.info(f"MainRouter | UI features loaded={len(feature_routers)}")
    return main_router

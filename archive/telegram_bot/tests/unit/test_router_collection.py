from types import SimpleNamespace

from aiogram import Router

from src.telegram_bot.core import routers as router_module


def test_collect_feature_routers_loads_redis_feature_routers(monkeypatch):
    telegram_router = Router(name="telegram_test_router")
    redis_router = Router(name="redis_test_router")

    def fake_import_module(module_path: str):
        if module_path == "src.telegram_bot.features.telegram.test.handlers":
            return SimpleNamespace(router=telegram_router)
        if module_path == "src.telegram_bot.features.redis.test.handlers":
            return SimpleNamespace(router=redis_router)
        raise ImportError(module_path)

    monkeypatch.setattr(router_module, "INSTALLED_FEATURES", ["features.telegram.test"])
    monkeypatch.setattr(router_module, "INSTALLED_REDIS_FEATURES", ["features.redis.test"])
    monkeypatch.setattr(router_module.importlib, "import_module", fake_import_module)

    assert router_module.collect_feature_routers() == [telegram_router, redis_router]

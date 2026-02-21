import json
from typing import Any

from src.shared.core.redis_service import RedisService

from .admin_keys import AdminKeys


class AdminCacheManager:
    """
    Менеджер для работы с кэшем админ-панели (сводки и JSON-дампы деталей).
    """

    def __init__(self, redis_service: RedisService, ttl: int = 3600):
        self.redis = redis_service
        self.ttl = ttl  # По умолчанию 1 час (3600 секунд)

    async def save_summary(self, domain: str, data: dict[str, Any]) -> None:
        """Сохраняет сводные данные (Summary) для конкретного домена."""
        key = AdminKeys.get_summary_key(domain)
        await self.redis.set_value(key, json.dumps(data, ensure_ascii=False), ttl=self.ttl)

    async def get_summary(self, domain: str) -> dict[str, Any] | None:
        """Получает сводные данные (Summary) для конкретного домена."""
        key = AdminKeys.get_summary_key(domain)
        data = await self.redis.get_value(key)
        if data:
            return json.loads(data)
        return None

    async def save_details(self, domain: str, data: list[dict[str, Any]]) -> None:
        """Сохраняет список детальных записей (Details) как JSON-дамп."""
        key = AdminKeys.get_details_key(domain)
        await self.redis.set_value(key, json.dumps(data, ensure_ascii=False), ttl=self.ttl)

    async def get_details(self, domain: str) -> list[dict[str, Any]] | None:
        """Получает JSON-дамп детальных записей."""
        key = AdminKeys.get_details_key(domain)
        data = await self.redis.get_value(key)
        if data:
            return json.loads(data)
        return None

    async def invalidate(self, domain: str) -> None:
        """Очищает кэш сводок и деталей по домену."""
        await self.redis.delete_key(AdminKeys.get_summary_key(domain))
        await self.redis.delete_key(AdminKeys.get_details_key(domain))

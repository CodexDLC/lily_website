import json
from typing import Any

from codex_platform.redis_service import RedisService

from .admin_keys import AdminKeys


class AdminCacheManager:
    """
    Менеджер для работы с кэшем админ-панели (сводки и JSON-дампы деталей).
    """

    def __init__(self, redis_service: RedisService, ttl: int = 3600):
        self.redis = redis_service
        self.ttl = ttl

    async def save_summary(self, domain: str, data: dict[str, Any]) -> None:
        key = AdminKeys.get_summary_key(domain)
        await self.redis.string.set(key, json.dumps(data, ensure_ascii=False), ttl=self.ttl)

    async def get_summary(self, domain: str) -> dict[str, Any] | None:
        key = AdminKeys.get_summary_key(domain)
        data = await self.redis.string.get(key)
        if data:
            return json.loads(data)
        return None

    async def save_details(self, domain: str, data: list[dict[str, Any]]) -> None:
        key = AdminKeys.get_details_key(domain)
        await self.redis.string.set(key, json.dumps(data, ensure_ascii=False), ttl=self.ttl)

    async def get_details(self, domain: str) -> list[dict[str, Any]] | None:
        key = AdminKeys.get_details_key(domain)
        data = await self.redis.string.get(key)
        if data:
            return json.loads(data)
        return None

    async def invalidate(self, domain: str) -> None:
        await self.redis.string.delete(AdminKeys.get_summary_key(domain))
        await self.redis.string.delete(AdminKeys.get_details_key(domain))

import json
from typing import Any

from src.shared.core.redis_service import RedisService

from .notification_keys import NotificationKeys


class ContactCacheManager:
    """
    Менеджер для временного кэширования данных контактных заявок в Redis.
    """

    def __init__(self, redis_service: RedisService, ttl: int = 86400):
        self.redis = redis_service
        self.ttl = ttl

    def _get_key(self, request_id: int | str) -> str:
        return NotificationKeys.get_contact_cache_key(request_id)

    async def save(self, request_id: int | str, data: dict[str, Any]) -> None:
        """Сохраняет данные контактной заявки в формате JSON."""
        key = self._get_key(request_id)
        await self.redis.set_value(key, json.dumps(data, ensure_ascii=False), ttl=self.ttl)

    async def get(self, request_id: int | str) -> dict[str, Any] | None:
        """Получает данные контактной заявки."""
        key = self._get_key(request_id)
        data = await self.redis.get_value(key)
        if data:
            return json.loads(data)
        return None

    async def delete(self, request_id: int | str) -> None:
        """Удаляет данные из кэша."""
        key = self._get_key(request_id)
        await self.redis.delete_key(key)

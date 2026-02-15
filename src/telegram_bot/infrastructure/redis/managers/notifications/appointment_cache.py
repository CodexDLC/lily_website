import json
from typing import Any

from src.shared.core.redis_service import RedisService

from .notification_keys import NotificationKeys


class AppointmentCacheManager:
    """
    Менеджер для временного кэширования данных заявок в Redis.
    """

    def __init__(self, redis_service: RedisService, ttl: int = 86400):
        self.redis = redis_service
        self.ttl = ttl

    def _get_key(self, appointment_id: int | str) -> str:
        return NotificationKeys.get_appointment_cache_key(appointment_id)

    async def save(self, appointment_id: int | str, data: dict[str, Any]) -> None:
        """Сохраняет данные заявки в формате JSON."""
        key = self._get_key(appointment_id)
        # В RedisService аргумент называется ttl
        await self.redis.set_value(key, json.dumps(data, ensure_ascii=False), ttl=self.ttl)

    async def get(self, appointment_id: int | str) -> dict[str, Any] | None:
        """Получает данные заявки."""
        key = self._get_key(appointment_id)
        data = await self.redis.get_value(key)
        if data:
            return json.loads(data)
        return None

    async def delete(self, appointment_id: int | str) -> None:
        """Удаляет данные из кэша."""
        key = self._get_key(appointment_id)
        await self.redis.delete_key(key)

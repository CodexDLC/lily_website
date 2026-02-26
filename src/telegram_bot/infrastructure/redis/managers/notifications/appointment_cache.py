import json
from typing import Any

from loguru import logger

from src.shared.core.redis_service import RedisService

from .notification_keys import NotificationKeys


class AppointmentCacheManager:
    """
    Manager for temporary caching of appointment data in Redis.
    """

    def __init__(self, redis_service: RedisService, ttl: int = 86400):
        self.redis = redis_service
        self.ttl = ttl

    def _get_key(self, appointment_id: int | str) -> str:
        return NotificationKeys.get_appointment_cache_key(appointment_id)

    async def save(self, appointment_id: int | str, data: dict[str, Any]) -> None:
        """Saves appointment data in JSON format."""
        key = self._get_key(appointment_id)
        logger.debug(f"Redis: AppointmentCache | Action: Save | appt_id={appointment_id} | ttl={self.ttl}")
        try:
            # In RedisService the argument is named ttl
            await self.redis.set_value(key, json.dumps(data, ensure_ascii=False), ttl=self.ttl)
            logger.info(f"Redis: AppointmentCache | Action: Success | appt_id={appointment_id}")
        except Exception as e:
            logger.error(f"Redis: AppointmentCache | Action: SaveFailed | appt_id={appointment_id} | error={e}")

    async def get(self, appointment_id: int | str) -> dict[str, Any] | None:
        """Retrieves appointment data."""
        key = self._get_key(appointment_id)
        logger.debug(f"Redis: AppointmentCache | Action: Get | appt_id={appointment_id}")
        try:
            data = await self.redis.get_value(key)
            if data:
                logger.debug(f"Redis: AppointmentCache | Action: CacheHit | appt_id={appointment_id}")
                return json.loads(data)
            logger.warning(f"Redis: AppointmentCache | Action: CacheMiss | appt_id={appointment_id}")
            return None
        except Exception as e:
            logger.error(f"Redis: AppointmentCache | Action: GetFailed | appt_id={appointment_id} | error={e}")
            return None

    async def delete(self, appointment_id: int | str) -> None:
        """Deletes data from cache."""
        key = self._get_key(appointment_id)
        logger.debug(f"Redis: AppointmentCache | Action: Delete | appt_id={appointment_id}")
        try:
            await self.redis.delete_key(key)
            logger.info(f"Redis: AppointmentCache | Action: SuccessDelete | appt_id={appointment_id}")
        except Exception as e:
            logger.error(f"Redis: AppointmentCache | Action: DeleteFailed | appt_id={appointment_id} | error={e}")

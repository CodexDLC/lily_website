import json
from typing import Any

from codex_platform.redis_service import RedisService
from loguru import logger

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
        key = self._get_key(appointment_id)
        logger.debug(f"Redis: AppointmentCache | Action: Save | appt_id={appointment_id} | ttl={self.ttl}")
        try:
            await self.redis.string.set(key, json.dumps(data, ensure_ascii=False), ttl=self.ttl)
            logger.info(f"Redis: AppointmentCache | Action: Success | appt_id={appointment_id}")
        except Exception as e:
            logger.error(f"Redis: AppointmentCache | Action: SaveFailed | appt_id={appointment_id} | error={e}")

    async def get(self, appointment_id: int | str) -> dict[str, Any] | None:
        key = self._get_key(appointment_id)
        logger.debug(f"Redis: AppointmentCache | Action: Get | appt_id={appointment_id}")
        try:
            data = await self.redis.string.get(key)
            if data:
                logger.debug(f"Redis: AppointmentCache | Action: CacheHit | appt_id={appointment_id}")
                return json.loads(data)
            logger.warning(f"Redis: AppointmentCache | Action: CacheMiss | appt_id={appointment_id}")
            return None
        except Exception as e:
            logger.error(f"Redis: AppointmentCache | Action: GetFailed | appt_id={appointment_id} | error={e}")
            return None

    async def delete(self, appointment_id: int | str) -> None:
        key = self._get_key(appointment_id)
        logger.debug(f"Redis: AppointmentCache | Action: Delete | appt_id={appointment_id}")
        try:
            await self.redis.string.delete(key)
            logger.info(f"Redis: AppointmentCache | Action: SuccessDelete | appt_id={appointment_id}")
        except Exception as e:
            logger.error(f"Redis: AppointmentCache | Action: DeleteFailed | appt_id={appointment_id} | error={e}")

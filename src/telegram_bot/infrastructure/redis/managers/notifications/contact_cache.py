import json
from typing import Any

from loguru import logger

from src.shared.core.redis_service import RedisService

from .notification_keys import NotificationKeys


class ContactCacheManager:
    """
    Manager for temporary caching of contact request data in Redis.
    """

    def __init__(self, redis_service: RedisService, ttl: int = 86400):
        self.redis = redis_service
        self.ttl = ttl

    def _get_key(self, request_id: int | str) -> str:
        return NotificationKeys.get_contact_cache_key(request_id)

    async def save(self, request_id: int | str, data: dict[str, Any]) -> None:
        """Saves contact request data in JSON format."""
        key = self._get_key(request_id)
        logger.debug(f"Redis: ContactCache | Action: Save | request_id={request_id} | ttl={self.ttl}")
        try:
            await self.redis.set_value(key, json.dumps(data, ensure_ascii=False), ttl=self.ttl)
            logger.info(f"Redis: ContactCache | Action: Success | request_id={request_id}")
        except Exception as e:
            logger.error(f"Redis: ContactCache | Action: SaveFailed | request_id={request_id} | error={e}")

    async def get(self, request_id: int | str) -> dict[str, Any] | None:
        """Retrieves contact request data."""
        key = self._get_key(request_id)
        logger.debug(f"Redis: ContactCache | Action: Get | request_id={request_id}")
        try:
            data = await self.redis.get_value(key)
            if data:
                logger.debug(f"Redis: ContactCache | Action: CacheHit | request_id={request_id}")
                return json.loads(data)
            logger.warning(f"Redis: ContactCache | Action: CacheMiss | request_id={request_id}")
            return None
        except Exception as e:
            logger.error(f"Redis: ContactCache | Action: GetFailed | request_id={request_id} | error={e}")
            return None

    async def delete(self, request_id: int | str) -> None:
        """Deletes data from cache."""
        key = self._get_key(request_id)
        logger.debug(f"Redis: ContactCache | Action: Delete | request_id={request_id}")
        try:
            await self.redis.delete_key(key)
            logger.info(f"Redis: ContactCache | Action: SuccessDelete | request_id={request_id}")
        except Exception as e:
            logger.error(f"Redis: ContactCache | Action: DeleteFailed | request_id={request_id} | error={e}")

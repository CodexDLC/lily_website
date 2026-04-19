from codex_platform.redis_service import RedisService
from redis.asyncio import Redis

from src.telegram_bot.infrastructure.redis.managers.notifications.appointment_cache import AppointmentCacheManager
from src.telegram_bot.infrastructure.redis.managers.notifications.contact_cache import ContactCacheManager
from src.telegram_bot.infrastructure.redis.managers.sender.sender_manager import SenderManager


class RedisContainer:
    """
    Контейнер для всех Redis-менеджеров.
    Обеспечивает единую точку доступа к слою данных Redis.
    """

    def __init__(self, redis_client: Redis):
        self.service = RedisService(redis_client)

        self.sender = SenderManager(self.service)
        self.appointment_cache = AppointmentCacheManager(self.service)
        self.contact_cache = ContactCacheManager(self.service)

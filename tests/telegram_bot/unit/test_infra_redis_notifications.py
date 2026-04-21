import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.telegram_bot.infrastructure.redis.managers.notifications.appointment_cache import AppointmentCacheManager
from src.telegram_bot.infrastructure.redis.managers.notifications.contact_cache import ContactCacheManager


@pytest.fixture
def mock_redis_service():
    service = MagicMock()
    service.string = AsyncMock()
    return service


class TestRedisNotificationCaches:
    @pytest.mark.asyncio
    async def test_appointment_cache_save_get_delete(self, mock_redis_service):
        manager = AppointmentCacheManager(mock_redis_service)
        data = {"id": 123, "name": "Test Appointment"}

        # Test Save
        await manager.save(123, data)
        mock_redis_service.string.set.assert_awaited_once_with(
            "notifications:cache:123", json.dumps(data, ensure_ascii=False), ttl=86400
        )

        # Test Get Hit
        mock_redis_service.string.get.return_value = json.dumps(data)
        result = await manager.get(123)
        assert result == data

        # Test Get Miss
        mock_redis_service.string.get.return_value = None
        result = await manager.get(456)
        assert result is None

        # Test Delete
        await manager.delete(123)
        mock_redis_service.string.delete.assert_awaited_once_with("notifications:cache:123")

    @pytest.mark.asyncio
    async def test_appointment_cache_errors(self, mock_redis_service):
        manager = AppointmentCacheManager(mock_redis_service)
        mock_redis_service.string.set.side_effect = Exception("Redis error")
        mock_redis_service.string.get.side_effect = Exception("Redis error")
        mock_redis_service.string.delete.side_effect = Exception("Redis error")

        # Should not raise, just log error
        await manager.save(1, {})
        assert await manager.get(1) is None
        await manager.delete(1)

    @pytest.mark.asyncio
    async def test_contact_cache_save_get_delete(self, mock_redis_service):
        manager = ContactCacheManager(mock_redis_service)
        data = {"request_id": "req-1", "user": "test_user"}

        # Test Save
        await manager.save("req-1", data)
        mock_redis_service.string.set.assert_awaited_once_with(
            "notifications:contact_cache:req-1", json.dumps(data, ensure_ascii=False), ttl=86400
        )

        # Test Get Hit
        mock_redis_service.string.get.return_value = json.dumps(data)
        result = await manager.get("req-1")
        assert result == data

        # Test Delete
        await manager.delete("req-1")
        mock_redis_service.string.delete.assert_awaited_once_with("notifications:contact_cache:req-1")

    @pytest.mark.asyncio
    async def test_contact_cache_full_cycle(self, mock_redis_service):
        manager = ContactCacheManager(mock_redis_service, ttl=100)
        data = {"test": 1}

        # Save success
        await manager.save("req1", data)
        mock_redis_service.string.set.assert_called_once()

        # Get hit
        mock_redis_service.string.get.return_value = json.dumps(data)
        assert await manager.get("req1") == data

        # Get miss (Line 39-40 coverage)
        mock_redis_service.string.get.return_value = None
        assert await manager.get("unknown") is None

        # Delete success
        await manager.delete("req1")
        mock_redis_service.string.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_contact_cache_errors_extended(self, mock_redis_service):
        manager = ContactCacheManager(mock_redis_service)

        # Save error (Line 28-29 coverage)
        mock_redis_service.string.set.side_effect = Exception("Fail")
        await manager.save("req1", {})

        # Get error
        mock_redis_service.string.get.side_effect = Exception("Fail")
        assert await manager.get("req1") is None

        # Delete error (Line 51-52 coverage)
        mock_redis_service.string.delete.side_effect = Exception("Fail")
        await manager.delete("req1")

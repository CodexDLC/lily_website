from unittest.mock import AsyncMock, MagicMock

import pytest

from src.telegram_bot.infrastructure.api_route.appointments import AppointmentsApiProvider
from src.telegram_bot.infrastructure.redis.managers.sender.sender_manager import SenderManager


class TestInfraApiRoute:
    @pytest.mark.asyncio
    async def test_appointments_api_provider_calls(self):
        mock_client = AsyncMock()
        provider = AppointmentsApiProvider(mock_client)

        # Test get_summary
        await provider.get_summary()
        mock_client._request.assert_awaited_with("GET", "/api/v1/booking/appointments/summary/")

        # Test get_list
        await provider.get_list("awaiting", page=2)
        mock_client._request.assert_awaited_with(
            "GET", "/api/v1/booking/appointments/list/?category_slug=awaiting&page=2"
        )

        # Test expire_reschedule
        await provider.expire_reschedule(123)
        mock_client._request.assert_awaited_with(
            "POST", "/api/v1/booking/appointments/expire/", json={"appointment_id": 123}
        )


class TestInfraRedisSender:
    @pytest.fixture
    def mock_redis_service(self):
        service = MagicMock()
        service.hash = AsyncMock()
        service.string = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_sender_manager_coords(self, mock_redis_service):
        manager = SenderManager(mock_redis_service)

        # Test update_coords (user)
        await manager.update_coords(123, {"menu": 1, "content": 2})
        mock_redis_service.hash.set_fields.assert_awaited_once_with("sender:user:123", {"menu": "1", "content": "2"})

        # Test update_coords (channel)
        mock_redis_service.hash.set_fields.reset_mock()
        await manager.update_coords("ch1", {"menu": 10}, is_channel=True)
        mock_redis_service.hash.set_fields.assert_awaited_once_with("sender:channel:ch1", {"menu": "10"})

        # Test get_coords
        mock_redis_service.hash.get_all.return_value = {"menu": "1", "invalid": "NaN"}
        coords = await manager.get_coords(123)
        assert coords == {"menu": 1}

        # Test clear_coords
        await manager.clear_coords(123)
        mock_redis_service.string.delete.assert_awaited_once_with("sender:user:123")

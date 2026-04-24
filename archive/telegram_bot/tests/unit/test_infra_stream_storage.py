from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.infrastructure.redis.stream_storage import CodexPlatformStreamStorage


@pytest.mark.asyncio
class TestCodexPlatformStreamStorage:
    @pytest.fixture
    def mock_redis(self):
        return MagicMock()

    @pytest.fixture
    def storage(self, mock_redis):
        with patch("src.telegram_bot.infrastructure.redis.stream_storage.StreamConsumer") as mock_consumer_cls:
            mock_consumer = AsyncMock()
            mock_consumer_cls.return_value = mock_consumer
            storage = CodexPlatformStreamStorage(mock_redis, "stream", "group", "consumer")
            return storage

    async def test_create_group(self, storage):
        await storage.create_group("any", "any")
        storage.consumer.ensure_group.assert_awaited_once()

    async def test_read_events(self, storage):
        # Setup mock events
        mock_event = MagicMock()
        mock_event.id = "1-0"
        mock_event.event_type = "test_type"
        mock_event.data = {"key": "value"}

        storage.consumer.read.return_value = [mock_event]

        events = await storage.read_events("any", "any", "any", count=10)

        assert len(events) == 1
        assert events[0][0] == "1-0"
        assert events[0][1]["type"] == "test_type"
        assert events[0][1]["key"] == "value"
        storage.consumer.read.assert_awaited_once_with(count=10)

    async def test_ack_event(self, storage):
        await storage.ack_event("any", "any", "msg-123")
        storage.consumer.ack.assert_awaited_once_with("msg-123")

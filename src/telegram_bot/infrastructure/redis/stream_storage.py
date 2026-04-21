from typing import Any

from codex_platform.streams import StreamConsumer
from redis.asyncio import Redis


class CodexPlatformStreamStorage:
    """Adapter from codex-platform StreamConsumer to codex-bot stream storage."""

    def __init__(
        self,
        redis_client: Redis,
        stream_name: str,
        consumer_group_name: str,
        consumer_name: str,
    ) -> None:
        self.consumer = StreamConsumer(redis_client, stream_name, consumer_group_name, consumer_name)

    async def create_group(self, stream_name: str, group_name: str) -> None:
        await self.consumer.ensure_group()

    async def read_events(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        count: int,
    ) -> list[tuple[str, dict[str, Any]]]:
        events = await self.consumer.read(count=count)
        return [(event.id, {"type": event.event_type, **event.data}) for event in events]

    async def ack_event(self, stream_name: str, group_name: str, message_id: str) -> None:
        await self.consumer.ack(message_id)

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from codex_platform.streams import StreamProducer

if TYPE_CHECKING:
    from redis.asyncio import Redis


class RedisStreams:
    class BotEvents:
        NAME = "bot_events"
        GROUP = "bot_group"
        CONSUMER_PREFIX = "bot_instance_"


class StreamManager:
    """Compatibility wrapper around codex-platform stream producer."""

    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client

    async def add_event(self, stream_name: str, payload: dict[str, Any]) -> str:
        event_type = str(payload.get("type") or "event")
        data = {key: value for key, value in payload.items() if key != "type"}
        return await StreamProducer(self.redis_client, stream_name).add_event(event_type, data)

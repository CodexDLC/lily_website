import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from codex_platform.streams import StreamConsumer
from loguru import logger as log
from redis.asyncio import Redis


class RedisStreamProcessor:
    """
    Процессор для чтения сообщений из Redis Stream.
    Использует StreamConsumer из codex_platform для работы с Redis.
    Отвечает за цикл опроса (Polling Loop) и вызов callback-функции.
    """

    def __init__(
        self,
        redis_client: Redis,
        stream_name: str,
        consumer_group_name: str,
        consumer_name: str,
        batch_count: int = 10,
        poll_interval: float = 1.0,
    ):
        self.consumer = StreamConsumer(redis_client, stream_name, consumer_group_name, consumer_name)
        self.stream_name = stream_name
        self.group_name = consumer_group_name
        self.batch_count = batch_count
        self.poll_interval = poll_interval

        self.is_running = False
        self._message_callback: Callable[[dict[str, Any]], Awaitable[None]] | None = None

    def set_message_callback(self, callback: Callable[[dict[str, Any]], Awaitable[None]]):
        self._message_callback = callback

    async def start_listening(self):
        if self.is_running:
            log.warning("RedisStreamProcessor is already running.")
            return

        for attempt in range(1, 6):
            try:
                await self.consumer.ensure_group()
                break
            except Exception as e:
                log.warning(f"RedisStreamProcessor | create_group attempt {attempt}/5 failed: {e}")
                if attempt < 5:
                    await asyncio.sleep(3)
                else:
                    log.error("RedisStreamProcessor | Failed to create group after 5 attempts, giving up.")
                    return

        self.is_running = True
        asyncio.create_task(self._consume_loop())
        log.info(f"RedisStreamProcessor started listening to '{self.stream_name}' as '{self.consumer.consumer}'")

    async def stop_listening(self):
        self.is_running = False
        log.info("RedisStreamProcessor stopped.")

    async def _consume_loop(self):
        while self.is_running:
            try:
                events = await self.consumer.read(count=self.batch_count)
                if not events:
                    await asyncio.sleep(self.poll_interval)
                    continue

                for event in events:
                    await self._process_single_event(event)

            except Exception as e:
                log.error(f"Error in RedisStreamProcessor loop: {e}")
                if "NOGROUP" in str(e):
                    log.warning("RedisStreamProcessor | Consumer group missing, recreating...")
                    try:
                        await self.consumer.ensure_group()
                        log.info("RedisStreamProcessor | Consumer group recreated successfully")
                    except Exception as create_err:
                        log.error(f"RedisStreamProcessor | Failed to recreate group: {create_err}")
                await asyncio.sleep(5)

    async def _process_single_event(self, event):
        try:
            if self._message_callback:
                data = {"type": event.event_type, **event.data}
                await self._message_callback(data)
            await self.consumer.ack(event.id)
        except Exception as e:
            log.error(f"Failed to process message {event.id}: {e}")

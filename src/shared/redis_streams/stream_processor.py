import asyncio
from collections.abc import Callable
from typing import Any, cast

import redis.asyncio as redis
from loguru import logger as log  # Используем loguru
from redis.asyncio.client import Redis


class RedisStreamProcessor:
    def __init__(
        self,
        redis_url: str,
        stream_name: str,
        consumer_group_name: str,
        consumer_name: str,
        block_ms: int = 5000,  # How long to block for new messages
        batch_size: int = 10,  # How many messages to read at once
    ):
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.consumer_group_name = consumer_group_name
        self.consumer_name = consumer_name
        self.block_ms = block_ms
        self.batch_size = batch_size

        self._redis_client: Redis | None = None
        self._message_callback: Callable[[dict[str, Any]], Any] | None = None  # Единый колбэк
        self._listening_task: asyncio.Task | None = None
        self._running = False

    async def _get_redis_client(self) -> Redis:
        if self._redis_client is None:
            self._redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self._redis_client

    async def connect(self):
        try:
            client = await self._get_redis_client()
            log.debug("Pinging Redis...")
            await client.ping()
            log.debug("Connected to Redis.")
        except redis.RedisError as e:
            log.error(f"Failed to connect to Redis: {e}")
            raise

    async def _create_consumer_group(self):
        client = await self._get_redis_client()
        try:
            # Create consumer group if it doesn't exist. MKSTREAM creates the stream if it doesn't exist.
            await client.xgroup_create(self.stream_name, self.consumer_group_name, id="0", mkstream=True)
            log.debug(f"Consumer group '{self.consumer_group_name}' created for stream '{self.stream_name}'.")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                log.debug(
                    f"Consumer group '{self.consumer_group_name}' already exists for stream '{self.stream_name}'."
                )
            else:
                log.error(f"Failed to create consumer group '{self.consumer_group_name}': {e}")
                raise

    def set_message_callback(self, callback: Callable[[dict[str, Any]], Any]):
        """Устанавливает единый колбэк для обработки всех сообщений из стрима."""
        self._message_callback = callback
        log.debug("Message callback set for RedisStreamProcessor.")

    async def _process_message(self, message_id: str, message_data: dict[str, Any]):
        """Передает сообщение в зарегистрированный колбэк."""
        if self._message_callback:
            try:
                log.debug(f"Passing message {message_id} to callback.")
                await self._message_callback(message_data)
                client = await self._get_redis_client()
                await client.xack(self.stream_name, self.consumer_group_name, message_id)
                log.debug(f"Message {message_id} acknowledged.")
            except Exception as e:
                log.error(
                    f"Error in message callback for message {message_id}: {e}",
                    exc_info=True,
                )
        else:
            log.warning(f"No message callback registered for RedisStreamProcessor. Message {message_id} not processed.")
            # Если нет колбэка, все равно подтверждаем, чтобы не забивать очередь
            client = await self._get_redis_client()
            await client.xack(self.stream_name, self.consumer_group_name, message_id)
            log.debug(f"Message {message_id} acknowledged without processing (no callback).")

    async def _listen_for_messages(self):
        """Main loop for listening to the Redis Stream."""
        client = await self._get_redis_client()
        while self._running:
            try:
                # Read messages from the stream using the consumer group
                # 'id': '>' means read new messages that have not been delivered to this group
                # '0-0' means read pending messages (messages that were delivered but not ACKed)
                response = await client.xreadgroup(
                    self.consumer_group_name,
                    self.consumer_name,
                    {self.stream_name: ">"},  # Read new messages
                    count=self.batch_size,
                    block=self.block_ms,
                )

                if response:
                    for _stream, messages in response:
                        for message_id, message_data in messages:
                            # message_data is a dict, but values might be bytes if not decoded
                            # Ensure message_data values are decoded if not already by redis client
                            decoded_data = {k: v for k, v in message_data.items()}
                            await self._process_message(message_id, decoded_data)
                else:
                    log.debug(f"No new messages in stream '{self.stream_name}'.")

            except redis.RedisError as e:
                log.error(f"Redis error during listening: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying
            except Exception as e:
                log.error(f"Unexpected error during listening: {e}", exc_info=True)
                await asyncio.sleep(1)  # Wait before retrying

    async def start_listening(self):
        """Starts the asynchronous listening task."""
        if self._running:
            log.warning("RedisStreamProcessor is already running.")
            return

        await self.connect()
        await self._create_consumer_group()

        self._running = True
        self._listening_task = asyncio.create_task(self._listen_for_messages())
        log.debug(
            f"RedisStreamProcessor started listening on stream '{self.stream_name}' with consumer group '{self.consumer_group_name}'."
        )

    async def stop_listening(self):
        """Stops the asynchronous listening task."""
        if not self._running:
            log.warning("RedisStreamProcessor is not running.")
            return

        self._running = False
        if self._listening_task:
            self._listening_task.cancel()
            try:
                await self._listening_task
            except asyncio.CancelledError:
                log.debug("RedisStreamProcessor listening task cancelled.")
            self._listening_task = None

        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
            log.debug("Redis client closed.")

        log.debug("RedisStreamProcessor stopped.")

    async def publish_message(self, message_type: str, payload: dict[str, Any]):
        """Publishes a message to the Redis Stream."""
        client = await self._get_redis_client()
        message_data = {"type": message_type, **payload}

        # Convert all values to strings to satisfy Redis type hints
        # Use cast(Any, ...) to bypass Mypy's strict type checking for xadd arguments
        redis_message_data = cast("Any", {k: str(v) for k, v in message_data.items()})

        try:
            message_id = await client.xadd(self.stream_name, redis_message_data)
            log.debug(f"Published message '{message_type}' with ID {message_id} to stream '{self.stream_name}'.")
            return message_id
        except redis.RedisError as e:
            log.error(f"Failed to publish message to Redis Stream: {e}", exc_info=True)
            raise

# 📜 Factory

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

This module provides the `build_bot` function, responsible for creating and configuring the `Bot` and `Dispatcher` instances for the Telegram bot application. It handles the initialization of the Aiogram bot, Redis storage, and ensures connectivity to Redis.

## `build_bot` Function

```python
async def build_bot(settings: BotSettings, redis_client: Redis) -> tuple[Bot, Dispatcher]:
```
Creates and configures the `Bot` and `Dispatcher` instances. This function is crucial for the bot's startup process, setting up its core components.

*   `settings` (`BotSettings`): An instance of `BotSettings` containing bot-specific configurations, such as the bot token.
*   `redis_client` (`Redis`): An asynchronous Redis client instance used for FSM (Finite State Machine) storage.

**Process:**
1.  **Bot Token Check:** Verifies that `BOT_TOKEN` is provided in the settings. If not, raises a `RuntimeError`.
2.  **Bot Initialization:** Creates an `aiogram.Bot` instance with the provided token and sets the default parse mode to HTML.
3.  **Redis Connectivity Check:** Performs a `ping` to the Redis client to ensure a successful connection. If the connection fails, a `RuntimeError` is raised.
4.  **Redis Storage Setup:** Initializes `RedisStorage` for the `Dispatcher`, using the provided Redis client. This enables the bot to store user states in Redis.
5.  **Dispatcher Initialization:** Creates an `aiogram.Dispatcher` instance, associating it with the configured Redis storage and bot settings.

**Returns:**
A tuple containing the initialized `Bot` and `Dispatcher` instances.

**Raises:**
*   `RuntimeError`: If `BOT_TOKEN` is not found or if there's a critical error connecting to Redis.

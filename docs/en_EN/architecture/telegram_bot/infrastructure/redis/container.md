# 📄 Redis Container

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

The `RedisContainer` is a centralized entry point for all Redis-related managers and services. It provides a unified interface for the bot's data persistence layer.

## 🛠️ Class: RedisContainer

Located in: `src/telegram_bot/infrastructure/redis/container.py`

This container is initialized once and injected into the bot's dependency injection (DI) system, making it accessible to all orchestrators and services.

### 🔍 Core Components

*   **`service: RedisService`**: A base wrapper around the Redis client, providing common operations like `set_value`, `get_value`, and `delete_key`.
*   **`sender: SenderManager`**: Manages UI coordinates (chat IDs, message IDs) to track and update bot messages.
*   **`appointment_cache: AppointmentCacheManager`**: Handles temporary caching of booking data for notifications and workers.

## 🧩 Why is this needed?

1.  **Single Source of Truth**: All Redis logic is grouped here, making it easy to manage connections and shared services.
2.  **Dependency Injection**: By injecting the container, we ensure that all parts of the bot use the same Redis client and manager instances.
3.  **Decoupling**: Orchestrators don't need to know how Redis keys are generated or how data is serialized; they simply call methods on the container's managers.

## 📝 Usage Example

```python
# Accessing the container from an orchestrator
await self.container.redis.appointment_cache.save(appointment_id, data)
await self.container.redis.sender.save_coordinates(chat_id, message_id)
```

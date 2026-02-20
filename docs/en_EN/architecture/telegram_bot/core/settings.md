# 📄 Bot Settings (Registry)

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

The `core/settings.py` file acts as a central registry for the bot's modular architecture. It defines which features and middlewares are active in the system.

## 🏗️ Configuration Lists

Located in: `src/telegram_bot/core/settings.py`

### `INSTALLED_FEATURES`
A list of features that provide a user interface via Telegram (handlers, routers, keyboards).
- **Purpose**: Used by `Router Discovery` to automatically assemble the bot's routing table.
- **Format**: Relative path from `src/telegram_bot/` (e.g., `features.telegram.commands`).

### `INSTALLED_REDIS_FEATURES`
A list of features that act as listeners for Redis Streams.
- **Purpose**: Used by the `RedisStreamProcessor` to route incoming events (like notifications from the backend) to the correct logic.
- **Format**: Relative path from `src/telegram_bot/` (e.g., `features.redis.notifications`).

### `MIDDLEWARE_CLASSES`
A list of middleware modules to be applied to the bot's dispatcher.
- **Purpose**: Defines the order and presence of global middlewares (e.g., security, throttling, DI container injection).
- **Format**: Full python path to the **module** containing a `setup` function (e.g., `middlewares.user_validation`).

> **Note**: `I18nMiddleware` is not included in this list because it is initialized and registered separately in `core/factory.py` to handle its specific configuration requirements (locales compilation, FSM manager).

## 🧩 Adding a New Feature

To register a new feature:
1.  Create the feature directory in `src/telegram_bot/features/`.
2.  Add the path to `INSTALLED_FEATURES` (if it has Telegram handlers) or `INSTALLED_REDIS_FEATURES` (if it listens to Redis).

Example:
```python
INSTALLED_FEATURES = [
    ...,
    "features.telegram.my_new_feature",
]
```

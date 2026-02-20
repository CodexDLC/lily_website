# 📄 Bot Factory

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

The `Bot Factory` is responsible for creating and configuring the core `aiogram` components: the `Bot` and the `Dispatcher`. It also handles the initialization of the internationalization (i18n) system.

## 🛠️ Core Functions

Located in: `src/telegram_bot/core/factory.py`

### 1. `compile_locales(base_path: pathlib.Path) -> str`

This helper function prepares the localization files for the `aiogram-i18n` engine.

*   **Process**:
    1.  Creates a temporary directory `/tmp/bot_locales/`.
    2.  Iterates through language folders (e.g., `ru`, `de`) in `src/telegram_bot/resources/locales/`.
    3.  Collects all `.ftl` (Fluent) files within each language folder.
    4.  Merges them into a single `messages.ftl` file per language in the temporary directory.
*   **Why?**: This allows for a modular structure of translation files while satisfying the requirement of the `FluentRuntimeCore` to have a single entry point per locale. It also ensures compatibility with Docker environments by using `/tmp`.

### 2. `build_bot(settings: BotSettings, redis_client: Redis) -> tuple[Bot, Dispatcher]`

The main entry point for bot initialization.

#### Responsibilities

1.  **Token Validation**: Checks if `BOT_TOKEN` is present in the settings. Raises a `RuntimeError` if missing.
2.  **Bot Initialization**: Creates an `aiogram.Bot` instance with `HTML` as the default parse mode.
3.  **Redis Connectivity Check**: Performs a `ping` on the provided Redis client to ensure the bot can store FSM states and handle caching.
4.  **Storage Setup**: Initializes `RedisStorage` using the verified Redis client.
5.  **I18n Setup**:
    *   Calls `compile_locales` to prepare translation files.
    *   Initializes `I18nMiddleware` using `FluentRuntimeCore`.
    *   Uses `FSMContextI18nManager` to manage user locales via FSM.
    *   Sets the default locale (e.g., `de`).
    *   Registers the middleware with the `Dispatcher`.
6.  **Dispatcher Initialization**: Creates an `aiogram.Dispatcher` instance, injecting the Redis storage and bot settings.

## 📝 Usage Example

```python
settings = BotSettings()
redis = Redis.from_url(settings.redis_url)

bot, dp = await build_bot(settings, redis)
```

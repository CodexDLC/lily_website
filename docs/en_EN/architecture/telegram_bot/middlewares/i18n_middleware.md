# 📄 I18n Middleware (FSM Manager)

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

The `I18n Middleware` is responsible for determining and managing the user's preferred language (locale) throughout the bot's lifecycle.

## 🛠️ Class: FSMContextI18nManager

Located in: `src/telegram_bot/middlewares/i18n_middleware.py`

This class extends `aiogram_i18n.managers.BaseManager` to provide a custom strategy for locale resolution and persistence.

### 🔍 Locale Resolution Strategy (`get_locale`)

When an update arrives, the manager determines the locale in the following order of priority:

1.  **FSM State (Redis)**: Checks if a `locale` key exists in the user's FSM data. This is the highest priority as it represents an explicit user choice.
2.  **Telegram User Data**: If no FSM data is found, it checks the `language_code` provided by the Telegram API. Currently supports `ru` and `de`.
3.  **Default Locale**: If neither of the above is available or supported, it defaults to `de` (German).

### 💾 Locale Persistence (`set_locale`)

When a user changes their language (e.g., via a settings menu), the `set_locale` method is called. It updates the user's FSM data with the new `locale` key, ensuring the choice persists across sessions.

## ⚙️ Integration

Unlike other middlewares, the `I18nMiddleware` is initialized and registered in `src/telegram_bot/core/factory.py` because it requires specific setup for the Fluent core and the FSM manager.

```python
i18n_middleware = I18nMiddleware(
    core=FluentRuntimeCore(path=locales_path),
    manager=FSMContextI18nManager(),
    default_locale="de",
)
i18n_middleware.setup(dp)
```

## 📝 Key Features

*   **Redis-backed**: Uses the bot's Redis storage for persistent locale settings.
*   **Automatic Detection**: Leverages Telegram's `language_code` for a seamless first-time experience.
*   **Logging**: Provides detailed debug logs for locale resolution sources.

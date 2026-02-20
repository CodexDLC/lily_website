# 📂 Localization (i18n)

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../README.md)

The `resources/locales` directory contains the translation files for the Telegram Bot, using the **Fluent** (.ftl) format and the `aiogram-i18n` library.

## 🏗️ Structure

Located in: `src/telegram_bot/resources/locales/`

The localization system is designed to be modular, allowing translations to be split into multiple files for better maintainability.

### 📁 Language Folders (`/ru`, `/de`, etc.)
Each supported language has its own directory containing specific translation modules:
- **`common.ftl`**: Shared strings (buttons like "Back", "Cancel", etc.).
- **`menu.ftl`**: Translations for the main dashboard and navigation.
- **`notifications.ftl`**: Strings for the booking notification system.
- **`welcome.ftl`**: Initial greeting messages.

### 📄 Root Files (`ru.ftl`, `de.ftl`)
These files act as the main entry points for each language, often including or referencing the modular files during the compilation process.

## 🔄 Compilation Process

Because `aiogram-i18n` (specifically `FluentRuntimeCore`) typically expects a single path per locale, the bot uses a custom compilation step in `core/factory.py`:

1.  **Source**: `src/telegram_bot/resources/locales/{lang}/*.ftl`
2.  **Process**: The `compile_locales` function merges all `.ftl` files from a language folder into a single content block.
3.  **Output**: A temporary file is created at `/tmp/bot_locales/{lang}/messages.ftl`.
4.  **Runtime**: The bot points its i18n engine to this temporary directory.

## 📝 Usage in Code

Translations are accessed using the `i18n` object or lazy-translation proxies:

```python
# In a handler
await message.answer(i18n.notifications.title())

# In a keyboard
builder.button(text=i18n.notifications.btn_delete())
```

## 🧩 Related Components

- **[📄 Bot Factory](../../core/factory.md)**: Handles the compilation and middleware setup.
- **[📄 I18n Middleware](../../middlewares/i18n_middleware.md)**: Manages user language preferences in Redis.

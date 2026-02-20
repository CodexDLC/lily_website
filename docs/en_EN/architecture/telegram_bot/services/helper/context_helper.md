# 📄 Context Helper

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

The `Context Helper` is a utility service designed to extract and normalize basic Telegram event data into a unified context object.

## 🛠️ Class: ContextHelper

Located in: `src/telegram_bot/services/helper/context_helper.py`

This class provides static methods for processing `Message` and `CallbackQuery` objects from the `aiogram` library.

### 🔍 Method: `extract_base_context(event: Message | CallbackQuery) -> BaseBotContext`

This method is the primary tool for creating a `BaseBotContext` DTO from any incoming Telegram event.

#### Key Responsibilities

1.  **Unified ID Extraction**: Extracts `user_id`, `chat_id`, `message_id`, and `message_thread_id` regardless of the event type.
2.  **Fallback Logic**:
    *   If `from_user` is missing (e.g., in channel posts or certain system messages), it uses `chat_id` as a fallback for `user_id`.
    *   This ensures that every event has a unique identifier for session management and Redis state keys, preventing collisions.
3.  **Thread Support**: Correctly identifies `message_thread_id` for bots operating in Telegram topics (forums).

## 📝 Usage Example

```python
from src.telegram_bot.services.helper.context_helper import ContextHelper

@router.callback_query()
async def my_handler(callback: CallbackQuery):
    context = ContextHelper.extract_base_context(callback)
    # context.user_id, context.chat_id, etc. are now available
```

## 🧩 Related Components

*   **[📄 BaseBotContext](../../base/context_dto.md)**: The DTO returned by this helper.
*   **[📄 View Sender](../sender/view_sender.md)**: Often uses the extracted context to send or update messages.

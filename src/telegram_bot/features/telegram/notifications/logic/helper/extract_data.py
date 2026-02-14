from aiogram.types import CallbackQuery, Message

from src.telegram_bot.features.telegram.notifications.resources.callbacks import NotificationsCallback
from src.telegram_bot.features.telegram.notifications.resources.dto import QueryContext


def extract_context(call: CallbackQuery, callback_data: NotificationsCallback) -> QueryContext:
    """
    Извлекает user_id, chat_id и message_thread_id из CallbackQuery
    и возвращает их в виде объекта Pydantic-модели CallbackQueryContext.

    Args:
        call: Объект CallbackQuery, полученный от Telegram.
        callback_data: Опциональный объект CallbackData (например, NotificationsCallback),
                       из которого можно извлечь дополнительные поля, если они нужны в модели.

    Returns:
        Объект CallbackQueryContext с извлеченными данными.
    """
    user_id = call.from_user.id
    chat_id = None
    message_thread_id = None

    if isinstance(call.message, Message):
        chat_id = call.message.chat.id
        message_thread_id = call.message.message_thread_id

    action = callback_data.action
    session_id = callback_data.session_id

    return QueryContext(
        user_id=user_id, chat_id=chat_id, message_thread_id=message_thread_id, action=action, session_id=session_id
    )

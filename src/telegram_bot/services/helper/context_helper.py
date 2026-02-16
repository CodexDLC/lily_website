from aiogram.types import CallbackQuery, Message

from src.telegram_bot.services.base.context_dto import BaseBotContext


class ContextHelper:
    """
    Хелпер для извлечения базового контекста из событий Telegram.
    """

    @staticmethod
    def extract_base_context(event: Message | CallbackQuery) -> BaseBotContext:
        """
        Извлекает базовые ID из сообщения или колбека.
        """
        if isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            chat_id = event.message.chat.id if event.message else user_id
            message_id = event.message.message_id if event.message else None
            thread_id = event.message.message_thread_id if event.message else None
        else:
            user_id = event.from_user.id if event.from_user else 0
            chat_id = event.chat.id
            message_id = event.message_id
            thread_id = event.message_thread_id

        return BaseBotContext(user_id=user_id, chat_id=chat_id, message_id=message_id, message_thread_id=thread_id)

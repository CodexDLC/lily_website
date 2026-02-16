from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callbacks import NotificationsCallback
from .texts import NotificationsTexts


def build_main_kb(booking_id: int | str, topic_id: int | None = None) -> InlineKeyboardMarkup:
    """
    Клавиатура для управления бронью (Подтвердить / Отклонить).

    Args:
        booking_id: ID записи
        topic_id: ID топика в Telegram (для редактирования сообщений)
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text=NotificationsTexts.BTN_APPROVE,
        callback_data=NotificationsCallback(action="approve", session_id=booking_id, topic_id=topic_id).pack(),
    )
    builder.button(
        text=NotificationsTexts.BTN_REJECT,
        callback_data=NotificationsCallback(action="reject", session_id=booking_id, topic_id=topic_id).pack(),
    )

    builder.adjust(2)
    return builder.as_markup()

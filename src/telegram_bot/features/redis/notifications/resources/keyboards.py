from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callbacks import NotificationsCallback
from .texts import NotificationsTexts


def build_main_kb(booking_id: int | str, topic_id: int | None = None) -> InlineKeyboardMarkup:
    """
    Основная клавиатура (Подтвердить / Отклонить).
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


def build_post_action_kb(booking_id: int | str, topic_id: int | None = None) -> InlineKeyboardMarkup:
    """
    Клавиатура после действия (только кнопка Удалить).
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🗑 Удалить",
        callback_data=NotificationsCallback(
            action="delete_notification", session_id=booking_id, topic_id=topic_id
        ).pack(),
    )

    return builder.as_markup()

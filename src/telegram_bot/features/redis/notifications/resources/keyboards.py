from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callbacks import NotificationsCallback
from .texts import NotificationsTexts


def build_main_kb(booking_id: int | str) -> InlineKeyboardMarkup:
    """
    Клавиатура для управления бронью (Подтвердить / Отклонить).
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text=NotificationsTexts.BTN_APPROVE,
        callback_data=NotificationsCallback(action="approve", session_id=booking_id).pack(),
    )
    builder.button(
        text=NotificationsTexts.BTN_REJECT,
        callback_data=NotificationsCallback(action="reject", session_id=booking_id).pack(),
    )

    builder.adjust(2)
    return builder.as_markup()

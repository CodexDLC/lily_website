from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callbacks import NotificationsCallback
from .texts import NotificationsTexts


def build_main_kb():
    """
    Клавиатура главного экрана.
    """
    builder = InlineKeyboardBuilder()

    builder.button(text=NotificationsTexts.BUTTON_ACTION, callback_data=NotificationsCallback(action="action").pack())

    # Пример кнопки назад (если нужна)
    # builder.button(
    #     text=NotificationsTexts.BUTTON_BACK,
    #     callback_data=NotificationsCallback(action="back").pack()
    # )

    builder.adjust(1)
    return builder.as_markup()

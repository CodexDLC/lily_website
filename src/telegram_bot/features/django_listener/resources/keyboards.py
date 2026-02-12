from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callbacks import DjangoListenerCallback
from .texts import DjangoListenerTexts


def build_main_kb():
    """
    Клавиатура главного экрана.
    """
    builder = InlineKeyboardBuilder()

    builder.button(text=DjangoListenerTexts.BUTTON_ACTION, callback_data=DjangoListenerCallback(action="action").pack())

    # Пример кнопки назад (если нужна)
    # builder.button(
    #     text=DjangoListenerTexts.BUTTON_BACK,
    #     callback_data=DjangoListenerCallback(action="back").pack()
    # )

    builder.adjust(1)
    return builder.as_markup()

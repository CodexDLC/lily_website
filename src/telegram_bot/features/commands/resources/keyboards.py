"""
Клавиатуры для фичи commands.
"""

from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.telegram_bot.features.commands.resources.callbacks import SettingsCallback


def build_start_keyboard():
    """Клавиатура стартового экрана."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Settings", callback_data=SettingsCallback(action="open").pack())
    builder.adjust(1)
    return builder.as_markup()

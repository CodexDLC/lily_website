from unittest.mock import MagicMock, patch

from aiogram.types import Chat, InlineKeyboardMarkup, Message, User

from src.telegram_bot.features.telegram.commands.resources.callbacks import SettingsCallback, SystemCallback
from src.telegram_bot.features.telegram.commands.resources.formatters import MessageInfoFormatter
from src.telegram_bot.features.telegram.commands.resources.keyboards import build_welcome_keyboard
from src.telegram_bot.features.telegram.commands.resources.texts import HELP_TEXT, WELCOME_ADMIN, WELCOME_USER


def test_callbacks_structure():
    """Проверка структуры CallbackData."""
    sys_cb = SystemCallback(action="logout")
    assert sys_cb.pack() == "sys:logout"

    settings_cb = SettingsCallback(action="toggle_notifications")
    assert settings_cb.pack() == "cmd_settings:toggle_notifications"


def test_message_info_formatter():
    """Проверка форматировщика инфо о сообщении."""
    mock_user = MagicMock(spec=User)
    mock_user.id = 123

    mock_chat = MagicMock(spec=Chat)
    mock_chat.id = 456

    mock_message = MagicMock(spec=Message)
    mock_message.from_user = mock_user
    mock_message.chat = mock_chat

    result = MessageInfoFormatter.format_chat_ids(mock_message)
    assert "User ID:</b> <code>123</code>" in result
    assert "Chat ID:</b> <code>456</code>" in result


def test_message_info_formatter_no_user():
    """Проверка случая, когда user_id недоступен."""
    mock_chat = MagicMock(spec=Chat)
    mock_chat.id = 456

    mock_message = MagicMock(spec=Message)
    mock_message.from_user = None
    mock_message.chat = mock_chat

    result = MessageInfoFormatter.format_chat_ids(mock_message)
    assert "User ID:</b> <code>N/A</code>" in result


@patch("aiogram_i18n.I18nContext.get_current")
def test_build_welcome_keyboard_user(mock_get_i18n):
    """Проверка сборки клавиатуры для обычного пользователя."""
    mock_i18n = MagicMock()
    mock_i18n.welcome.btn.launch.return_value = "Launch"
    mock_get_i18n.return_value = mock_i18n

    kb = build_welcome_keyboard(is_admin=False)
    assert isinstance(kb, InlineKeyboardMarkup)
    # 1 кнопка (launch)
    assert len(kb.inline_keyboard) == 1
    assert kb.inline_keyboard[0][0].text == "Launch"


@patch("aiogram_i18n.I18nContext.get_current")
def test_build_welcome_keyboard_admin(mock_get_i18n):
    """Проверка сборки клавиатуры для администратора."""
    mock_i18n = MagicMock()
    mock_i18n.welcome.btn.launch.return_value = "Launch"
    mock_i18n.welcome.btn.admin.return_value = "Admin Panel"
    mock_get_i18n.return_value = mock_i18n

    kb = build_welcome_keyboard(is_admin=True)
    assert isinstance(kb, InlineKeyboardMarkup)
    # 2 кнопки (launch + admin), каждая в своем ряду (adjust 1)
    assert len(kb.inline_keyboard) == 2
    assert kb.inline_keyboard[0][0].text == "Launch"
    assert kb.inline_keyboard[1][0].text == "Admin Panel"


def test_texts_availability():
    """Проверка доступности строковых констант."""
    assert "{name}" in WELCOME_USER
    assert "{name}" in WELCOME_ADMIN
    assert "Help Center" in HELP_TEXT

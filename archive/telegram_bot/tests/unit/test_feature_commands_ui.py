from unittest.mock import MagicMock, patch

from aiogram.types import InlineKeyboardMarkup
from codex_bot.base import ViewResultDTO

from src.telegram_bot.features.telegram.commands.ui.commands_ui import CommandsUI


class TestCommandsUI:
    @patch("aiogram_i18n.I18nContext.get_current")
    @patch("src.telegram_bot.features.telegram.commands.ui.commands_ui.build_welcome_keyboard")
    def test_render_welcome_screen_admin(self, mock_build_kb, mock_get_i18n):
        # Setup mock i18n
        mock_i18n = MagicMock()
        mock_i18n.welcome.admin.return_value = "Welcome Admin"
        mock_get_i18n.return_value = mock_i18n

        # Setup real keyboard for pydantic validation
        real_kb = InlineKeyboardMarkup(inline_keyboard=[])
        mock_build_kb.return_value = real_kb

        ui = CommandsUI()
        result = ui.render_welcome_screen("Boss", is_admin=True)

        assert isinstance(result, ViewResultDTO)
        assert result.text == "Welcome Admin"
        assert result.kb == real_kb
        mock_i18n.welcome.admin.assert_called_once_with(name="Boss")
        mock_build_kb.assert_called_once_with(is_admin=True)

    @patch("aiogram_i18n.I18nContext.get_current")
    @patch("src.telegram_bot.features.telegram.commands.ui.commands_ui.build_welcome_keyboard")
    def test_render_welcome_screen_user(self, mock_build_kb, mock_get_i18n):
        mock_i18n = MagicMock()
        mock_i18n.welcome.user.return_value = "Hello User"
        mock_get_i18n.return_value = mock_i18n

        # Setup real keyboard for pydantic validation
        real_kb = InlineKeyboardMarkup(inline_keyboard=[])
        mock_build_kb.return_value = real_kb

        ui = CommandsUI()
        result = ui.render_welcome_screen("Guest", is_admin=False)

        assert isinstance(result, ViewResultDTO)
        assert result.text == "Hello User"
        assert result.kb == real_kb
        mock_i18n.welcome.user.assert_called_once_with(name="Guest")
        mock_build_kb.assert_called_once_with(is_admin=False)

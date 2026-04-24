from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import InlineKeyboardMarkup
from codex_bot.base import UnifiedViewDTO, ViewResultDTO
from codex_bot.director import Director

from src.telegram_bot.features.telegram.bot_menu.logic.orchestrator import BotMenuOrchestrator
from src.telegram_bot.features.telegram.bot_menu.resources.dto import MenuContext
from src.telegram_bot.features.telegram.bot_menu.resources.keyboards import build_dashboard_keyboard
from src.telegram_bot.features.telegram.bot_menu.ui.menu_ui import BotMenuUI


@pytest.fixture(autouse=True)
def mock_i18n_global():
    mock_i18n = MagicMock()
    # Mocking terminal calls to return strings
    mock_i18n.menu.btn.back.to.user.return_value = "Back"
    mock_i18n.menu.admin.title.return_value = "Admin Dashboard"
    mock_i18n.menu.dashboard.title.return_value = "User Dashboard"
    with patch("aiogram_i18n.I18nContext.get_current", return_value=mock_i18n):
        yield mock_i18n


@pytest.fixture
def mock_discovery():
    discovery = MagicMock()
    discovery.get_menu_buttons.return_value = {
        "feat1": {"text": "Feature 1", "icon": "🚀", "priority": 10, "key": "feat1", "target_state": "state1"},
        "feat2": {"text": "Feature 2", "icon": "🛠", "priority": 20, "key": "feat2"},
    }
    return discovery


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.owner_ids_list = [123]
    settings.superuser_ids_list = [456]
    return settings


@pytest.fixture
def orchestrator(mock_discovery, mock_settings):
    return BotMenuOrchestrator(mock_discovery, mock_settings)


@pytest.fixture
def mock_director():
    director = MagicMock(spec=Director)
    director.session_key = "123"
    director.context_id = "789"
    director.set_scene = AsyncMock()
    return director


@pytest.mark.asyncio
class TestBotMenuOrchestrator:
    async def test_render_content_user(self, orchestrator, mock_director):
        mock_director.session_key = "999"  # Not admin
        view = await orchestrator.render_content(director=mock_director, payload="dashboard_admin")

        # Should fall back to user menu
        assert "Доступные функции" in view.text
        orchestrator.discovery.get_menu_buttons.assert_any_call(is_admin=False)

    async def test_handle_callback_open(self, orchestrator, mock_director):
        ctx = MenuContext(user_id=123, chat_id=789, action="open", target="some_menu")
        with patch.object(orchestrator, "handle_entry", new_callable=AsyncMock) as mock_entry:
            await orchestrator.handle_callback(mock_director, ctx)
            mock_entry.assert_awaited_once_with(mock_director, payload="some_menu")

    async def test_handle_callback_select(self, orchestrator, mock_director):
        ctx = MenuContext(user_id=123, chat_id=789, action="select", target="feat1")
        with patch.object(orchestrator, "handle_menu_click", new_callable=AsyncMock) as mock_click:
            await orchestrator.handle_callback(mock_director, ctx)
            mock_click.assert_awaited_once_with(mock_director, "feat1")

    async def test_render_dashboard_admin_success(self, orchestrator):
        view_dto = await orchestrator.render_dashboard(user_id=123, chat_id=789, mode="dashboard_admin")
        assert isinstance(view_dto, UnifiedViewDTO)
        assert view_dto.chat_id == 789
        orchestrator.discovery.get_menu_buttons.assert_called_with(is_admin=True)

    async def test_handle_menu_click_feature_transition(self, orchestrator, mock_director):
        # Click on feat1 (configured with state1)
        await orchestrator.handle_menu_click(mock_director, "feat1")
        mock_director.set_scene.assert_awaited_once_with(feature="state1", payload=None)

    async def test_handle_menu_click_dashboard_switch(self, orchestrator, mock_director):
        # Switch to admin dashboard
        view_dto = await orchestrator.handle_menu_click(mock_director, "dashboard_admin")
        assert view_dto.session_key == 123
        orchestrator.discovery.get_menu_buttons.assert_called_with(is_admin=True)


class TestBotMenuUI:
    def test_render_dashboard_content(self, mock_discovery):
        ui = BotMenuUI()
        buttons = mock_discovery.get_menu_buttons()

        with patch("src.telegram_bot.features.telegram.bot_menu.ui.menu_ui.build_dashboard_keyboard") as mock_kb:
            mock_kb.return_value = MagicMock(spec=InlineKeyboardMarkup)
            with patch(
                "src.telegram_bot.features.telegram.bot_menu.ui.menu_ui.get_dashboard_title", return_value="Title"
            ):
                result = ui.render_dashboard(buttons, mode="bot_menu")

                assert isinstance(result, ViewResultDTO)
                assert "Title" in result.text
                assert "🚀 <b>Feature 1</b>" in result.text
                assert "🛠 <b>Feature 2</b>" in result.text


@pytest.mark.asyncio
async def test_build_dashboard_keyboard_logic(mock_discovery, mock_i18n_global):
    buttons = mock_discovery.get_menu_buttons()

    # Admin mode
    kb = build_dashboard_keyboard(buttons, mode="dashboard_admin")
    assert isinstance(kb, InlineKeyboardMarkup)
    # Check that we have buttons for 2 features + 1 back button
    all_buttons = [btn for row in kb.inline_keyboard for btn in row]
    assert len(all_buttons) == 3
    assert all_buttons[-1].text == "Back"

    # User mode
    kb_user = build_dashboard_keyboard(buttons, mode="bot_menu")
    all_buttons_user = [btn for row in kb_user.inline_keyboard for btn in row]
    assert len(all_buttons_user) == 2

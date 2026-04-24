from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import InlineKeyboardMarkup, User
from codex_bot.base import ViewResultDTO
from codex_bot.director import Director

from src.telegram_bot.features.telegram.commands.logic.orchestrator import StartOrchestrator
from src.telegram_bot.features.telegram.commands.resources.dto import UserUpsertDTO


@pytest.fixture
def mock_auth():
    return AsyncMock()


@pytest.fixture
def mock_ui():
    ui = MagicMock()
    # Return a real ViewResultDTO to satisfy Pydantic validation in UnifiedViewDTO
    ui.render_welcome_screen.return_value = ViewResultDTO(text="Welcome", kb=InlineKeyboardMarkup(inline_keyboard=[]))
    return ui


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.owner_ids_list = [100]
    settings.superuser_ids_list = [200]
    return settings


@pytest.fixture
def orchestrator(mock_auth, mock_ui, mock_settings):
    return StartOrchestrator(mock_auth, mock_ui, mock_settings)


class TestStartOrchestrator:
    @pytest.mark.asyncio
    async def test_render_content_admin(self, orchestrator, mock_ui):
        director = MagicMock(spec=Director)
        director.session_key = 100  # Admin

        await orchestrator.render_content(director, payload="Dave")
        mock_ui.render_welcome_screen.assert_called_once_with("Dave", is_admin=True)

    @pytest.mark.asyncio
    async def test_render_content_user(self, orchestrator, mock_ui):
        director = MagicMock(spec=Director)
        director.session_key = 999  # Regular user

        await orchestrator.render_content(director, payload="John")
        mock_ui.render_welcome_screen.assert_called_once_with("John", is_admin=False)

    @pytest.mark.asyncio
    async def test_handle_entry_with_user(self, orchestrator, mock_auth):
        director = MagicMock(spec=Director)
        director.session_key = 123
        director.context_id = 456

        user = MagicMock(spec=User)
        user.id = 123
        user.first_name = "Alice"
        user.username = "alice_test"
        user.last_name = None
        user.language_code = "en"
        user.is_premium = False

        await orchestrator.handle_entry(director, payload=user)

        # Verify upsert
        mock_auth.upsert_user.assert_awaited_once()
        args, _ = mock_auth.upsert_user.call_args
        dto = args[0]
        assert isinstance(dto, UserUpsertDTO)
        assert dto.telegram_id == 123
        assert dto.first_name == "Alice"

    @pytest.mark.asyncio
    async def test_handle_entry_no_user(self, orchestrator, mock_auth, mock_ui):
        director = MagicMock(spec=Director)
        director.session_key = 123
        director.context_id = 123

        await orchestrator.handle_entry(director, payload=None)

        mock_auth.upsert_user.assert_not_awaited()
        mock_ui.render_welcome_screen.assert_called_once_with("User", is_admin=False)

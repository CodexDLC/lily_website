from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Chat, Message, User

from src.telegram_bot.features.telegram.commands.handlers.router import cmd_menu, cmd_start


@pytest.fixture
def mock_container():
    container = MagicMock()
    container.features = {}
    container.view_sender = AsyncMock()
    return container


@pytest.fixture
def mock_state():
    return MagicMock(spec=FSMContext)


@pytest.fixture
def mock_message():
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123
    message.from_user.username = "test_user"
    message.from_user.first_name = "Test"
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 456
    message.message_id = 789
    return message


class TestCommandHandlers:
    @pytest.mark.asyncio
    async def test_cmd_start_success(self, mock_message, mock_state, mock_container):
        # Setup orchestrator
        mock_orchestrator = AsyncMock()
        mock_orchestrator.handle_entry.return_value = MagicMock()
        mock_container.features["commands"] = mock_orchestrator

        await cmd_start(mock_message, mock_state, mock_container)

        # Verify orchestrator call
        mock_orchestrator.handle_entry.assert_awaited_once()
        _, kwargs = mock_orchestrator.handle_entry.call_args
        assert kwargs["payload"] == mock_message.from_user

        # Verify sender call
        mock_container.view_sender.send.assert_awaited_once_with(mock_orchestrator.handle_entry.return_value)

    @pytest.mark.asyncio
    async def test_cmd_menu_success(self, mock_message, mock_state, mock_container):
        # Setup orchestrator
        mock_orchestrator = AsyncMock()
        mock_orchestrator.handle_entry.return_value = MagicMock()
        mock_container.features["bot_menu"] = mock_orchestrator

        await cmd_menu(mock_message, mock_state, mock_container)

        # Verify orchestrator call
        mock_orchestrator.handle_entry.assert_awaited_once()

        # Verify sender call
        mock_container.view_sender.send.assert_awaited_once_with(mock_orchestrator.handle_entry.return_value)

    @pytest.mark.asyncio
    async def test_cmd_start_no_orchestrator(self, mock_message, mock_state, mock_container):
        mock_container.features = {}  # Empty

        # Should not raise, just log error internally
        await cmd_start(mock_message, mock_state, mock_container)

        mock_container.view_sender.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cmd_start_no_user(self, mock_message, mock_state, mock_container):
        mock_message.from_user = None

        await cmd_start(mock_message, mock_state, mock_container)

        mock_container.view_sender.send.assert_not_awaited()

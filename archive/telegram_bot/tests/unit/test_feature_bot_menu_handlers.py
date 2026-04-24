from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Chat, Message, User

from src.telegram_bot.features.telegram.bot_menu.handlers.menu_handlers import handle_dashboard_callback
from src.telegram_bot.features.telegram.bot_menu.resources.callbacks import DashboardCallback


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
def mock_call():
    call = MagicMock(spec=CallbackQuery)
    call.id = "test_call_id"
    call.from_user = MagicMock(spec=User)
    call.from_user.id = 111
    call.message = MagicMock(spec=Message)
    call.message.message_id = 222
    call.message.message_thread_id = None
    call.message.chat = MagicMock(spec=Chat)
    call.message.chat.id = 333
    call.answer = AsyncMock()
    return call


@pytest.mark.asyncio
async def test_handle_dashboard_callback_success(mock_call, mock_state, mock_container):
    # Setup
    mock_orchestrator = AsyncMock()
    mock_orchestrator.handle_callback.return_value = MagicMock()
    mock_container.features["bot_menu"] = mock_orchestrator

    cb_data = DashboardCallback(action="open", target="main")

    # Execute
    await handle_dashboard_callback(mock_call, cb_data, mock_state, mock_container)

    # Assert
    mock_call.answer.assert_awaited_once()
    mock_orchestrator.handle_callback.assert_awaited_once()
    mock_container.view_sender.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_dashboard_callback_no_orchestrator(mock_call, mock_state, mock_container):
    # Setup
    mock_container.features = {}  # No bot_menu
    cb_data = DashboardCallback(action="open", target="main")

    # Execute
    await handle_dashboard_callback(mock_call, cb_data, mock_state, mock_container)

    # Assert
    mock_call.answer.assert_awaited_once()
    mock_container.view_sender.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_dashboard_callback_orchestrator_returns_none(mock_call, mock_state, mock_container):
    # Setup
    mock_orchestrator = AsyncMock()
    mock_orchestrator.handle_callback.return_value = None
    mock_container.features["bot_menu"] = mock_orchestrator

    cb_data = DashboardCallback(action="action", target="some_target")

    # Execute
    await handle_dashboard_callback(mock_call, cb_data, mock_state, mock_container)

    # Assert
    mock_container.view_sender.send.assert_not_awaited()

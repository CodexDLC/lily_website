from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message

from src.telegram_bot.core.security import SecurityMiddleware


@pytest.mark.asyncio
class TestSecurityMiddleware:
    async def test_bypass_if_no_user_or_state(self):
        middleware = SecurityMiddleware()
        handler = AsyncMock()
        event = MagicMock()

        # Test no user
        await middleware(handler, event, {"state": AsyncMock()})
        handler.assert_called_once()

        handler.reset_mock()

        # Test no state
        await middleware(handler, event, {"user": MagicMock()})
        handler.assert_called_once()

    async def test_success_if_ids_match(self):
        middleware = SecurityMiddleware()
        handler = AsyncMock()
        event = MagicMock()
        user = MagicMock(id=123)
        state = AsyncMock()
        # Ensure state.get_data() returns an awaitable that results in the dict
        state.get_data = AsyncMock(return_value={"session_data": {"user_id": 123}})

        await middleware(handler, event, {"user": user, "state": state})
        handler.assert_called_once_with(event, {"user": user, "state": state})

    async def test_block_if_ids_mismatch_callback(self):
        middleware = SecurityMiddleware()
        handler = AsyncMock()
        # Use a real instance of CallbackQuery or a properly configured mock
        # to pass isinstance(event, CallbackQuery)
        event = MagicMock(spec=CallbackQuery)
        event.answer = AsyncMock()

        user = MagicMock(id=123)
        state = AsyncMock()
        state.get_data = AsyncMock(return_value={"session_data": {"user_id": 456}})

        result = await middleware(handler, event, {"user": user, "state": state})

        assert result is None
        handler.assert_not_called()
        event.answer.assert_called_once_with("⛔ Ошибка безопасности. Сессия не принадлежит вам.", show_alert=True)

    async def test_block_if_ids_mismatch_other_event(self):
        middleware = SecurityMiddleware()
        handler = AsyncMock()
        event = MagicMock(spec=Message)
        user = MagicMock(id=123)
        state = AsyncMock()
        state.get_data = AsyncMock(return_value={"session_data": {"user_id": 456}})

        result = await middleware(handler, event, {"user": user, "state": state})

        assert result is None
        handler.assert_not_called()

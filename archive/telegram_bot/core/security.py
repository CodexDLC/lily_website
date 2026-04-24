from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject
from loguru import logger as log

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext


class SecurityMiddleware(BaseMiddleware):
    """Project-specific FSM session ownership check."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("user")
        state: FSMContext | None = data.get("state")

        if not user or not state:
            return await handler(event, data)

        state_data = await state.get_data()
        session_data = state_data.get("session_data", {})
        stored_user_id = session_data.get("user_id")

        if stored_user_id and stored_user_id != user.id:
            log.error(
                "Security: user_id mismatch! "
                f"event_user={user.id} stored_user={stored_user_id} | "
                "Possible session hijacking attempt"
            )
            if isinstance(event, CallbackQuery):
                await event.answer("⛔ Ошибка безопасности. Сессия не принадлежит вам.", show_alert=True)
            return None

        return await handler(event, data)

from typing import Any

from aiogram.types import CallbackQuery

from src.telegram_bot.services.base.base_orchestrator import BaseBotOrchestrator
from src.telegram_bot.services.base.view_dto import UnifiedViewDTO

from ..contracts.contract import NotificationsDataProvider
from ..feature_setting import NotificationsStates
from ..resources.callbacks import NotificationsCallback
from ..resources.dto import QueryContext
from ..ui.ui import NotificationsUI
from .helper.extract_data import extract_context


class NotificationsOrchestrator(BaseBotOrchestrator):
    """
    Оркестратор для фичи Notifications (Telegram UI).
    """

    def __init__(self, data_provider: NotificationsDataProvider | None = None):
        super().__init__(expected_state="notifications")
        self.ui = NotificationsUI()
        self.data_provider = data_provider

    async def handle_action(self, callback_data: NotificationsCallback, call: CallbackQuery) -> UnifiedViewDTO:
        if not callback_data or not call or not callback_data.action:
            return UnifiedViewDTO(
                alert_text="Неизвестное действие",
            )

        context: QueryContext = extract_context(call, callback_data)

        if context.action == "approve":
            data = await self._handler_approve(context)
        elif context.action == "reject":
            data = await self._handler_reject(context)
        else:
            data = UnifiedViewDTO(
                alert_text="Неизвестное действие",
                chat_id=context.chat_id,
                session_key=context.user_id,
                mode="topic",
                message_thread_id=context.message_thread_id,
            )

        return data

    async def _handler_approve(self, context: QueryContext) -> UnifiedViewDTO:
        return UnifiedViewDTO(chat_id=context.chat_id, message_thread_id=context.message_thread_id)

    async def _handler_reject(self, context: QueryContext) -> UnifiedViewDTO:
        return UnifiedViewDTO(chat_id=context.chat_id, message_thread_id=context.message_thread_id)

    async def handle_entry(self, user_id: int, payload: Any = None) -> UnifiedViewDTO:
        """Вход в фичу (Cold Start)."""
        if self.director and self.director.state:
            await self.director.state.set_state(NotificationsStates.main)

        # Если провайдера нет, возвращаем пустой экран или ошибку
        if not self.data_provider:
            return UnifiedViewDTO(alert_text="Провайдер данных не настроен")

        user_notifications = await self.data_provider.get_data(user_id)
        return await self.render(user_notifications)

    async def render_content(self, payload: Any) -> Any:
        """Рендеринг основного контента."""
        return self.ui.render_main(payload) if payload else None

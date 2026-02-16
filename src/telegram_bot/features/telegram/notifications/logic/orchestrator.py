import functools
from typing import TYPE_CHECKING, Any

from aiogram.types import CallbackQuery
from loguru import logger as log

from src.telegram_bot.core.api_client import BaseApiClient
from src.telegram_bot.services.base.base_orchestrator import BaseBotOrchestrator
from src.telegram_bot.services.base.view_dto import UnifiedViewDTO

from ..contracts.contract import NotificationsDataProvider
from ..resources.callbacks import NotificationsCallback
from ..resources.dto import QueryContext
from ..resources.texts import NotificationsTexts
from ..ui.ui import NotificationsUI
from .helper.extract_data import extract_context
from .service import NotificationsService

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from src.telegram_bot.core.container import BotContainer


class NotificationsOrchestrator(BaseBotOrchestrator):
    """
    Оркестратор для фичи Notifications.
    """

    def __init__(
        self,
        container: "BotContainer",
        django_api: BaseApiClient,
        data_provider: NotificationsDataProvider | None = None,
    ):
        super().__init__(expected_state="notifications")
        self.container = container
        self.django_api = django_api
        self.ui = NotificationsUI()

        if not data_provider:
            raise ValueError("NotificationsDataProvider is required")

        self.service = NotificationsService(container, data_provider)
        self.settings = container.settings

    async def handle_action(self, callback_data: NotificationsCallback, call: CallbackQuery) -> UnifiedViewDTO:
        if not callback_data or not call or not callback_data.action:
            return UnifiedViewDTO(alert_text="Неизвестное действие")

        context: QueryContext = extract_context(call, callback_data)

        # Используем строковые аннотации для типов из TYPE_CHECKING
        action_map: dict[str, Callable[[QueryContext], Awaitable[UnifiedViewDTO]]] = {
            "approve": self._handler_approve,
            "reject": self._handler_reject,
            "reject_busy": functools.partial(
                self._reject_with_reason,
                reason_code="master_busy",
                reason_text=NotificationsTexts.EMAIL_REJECT_REASON_BUSY,
            ),
            "reject_ill": functools.partial(
                self._reject_with_reason,
                reason_code="master_ill",
                reason_text=NotificationsTexts.EMAIL_REJECT_REASON_ILL,
            ),
            "reject_materials": functools.partial(
                self._reject_with_reason,
                reason_code="no_materials",
                reason_text=NotificationsTexts.EMAIL_REJECT_REASON_MATERIALS,
            ),
            "reject_blacklist": functools.partial(
                self._reject_with_reason,
                reason_code="client_blacklist",
                reason_text=NotificationsTexts.EMAIL_REJECT_REASON_BLACKLIST,
            ),
            "cancel_reject": self._handler_cancel_reject,
            "delete_notification": self._handler_delete_notification,
        }

        handler = action_map.get(context.action)
        if handler:
            return await handler(context)
        return UnifiedViewDTO(alert_text="Неизвестное действие")

    async def _handler_approve(self, context: QueryContext) -> UnifiedViewDTO:
        if context.session_id is None:
            return UnifiedViewDTO(alert_text="Ошибка: ID не найден")

        appointment_id = int(context.session_id)

        try:
            response = await self.service.confirm_appointment(appointment_id)
            if not response.get("success"):
                return UnifiedViewDTO(
                    alert_text=f"Ошибка: {response.get('message')}",
                    chat_id=self.settings.telegram_admin_channel_id,
                    session_key=appointment_id,
                )

            updated_text = f"{NotificationsTexts.status_approved()}\n\n{context.message_text or ''}"
            return UnifiedViewDTO(
                content=self.ui.render_post_action(updated_text, appointment_id, context.message_thread_id),
                chat_id=self.settings.telegram_admin_channel_id,
                session_key=appointment_id,
                message_thread_id=context.message_thread_id,
                mode="edit",
                alert_text=NotificationsTexts.alert_approved(),
            )
        except Exception as e:
            log.error(f"Orchestrator | Approve error: {e}")
            return UnifiedViewDTO(
                alert_text=NotificationsTexts.error_api(),
                chat_id=self.settings.telegram_admin_channel_id,
                session_key=appointment_id,
            )

    async def _handler_reject(self, context: QueryContext) -> UnifiedViewDTO:
        if context.session_id is None:
            return UnifiedViewDTO(alert_text="Ошибка: ID не найден")

        appointment_id = int(context.session_id)
        return UnifiedViewDTO(
            content=self.ui.render_reject_reasons(appointment_id, context.message_thread_id),
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=appointment_id,
            message_thread_id=context.message_thread_id,
            mode="edit",
        )

    async def _reject_with_reason(self, context: QueryContext, reason_code: str, reason_text: str) -> UnifiedViewDTO:
        if context.session_id is None:
            return UnifiedViewDTO(alert_text="Ошибка: ID не найден")

        appointment_id = int(context.session_id)
        try:
            response = await self.service.cancel_appointment(appointment_id, reason_code, reason_text)
            if not response.get("success"):
                return UnifiedViewDTO(
                    alert_text=f"Ошибка: {response.get('message')}",
                    chat_id=self.settings.telegram_admin_channel_id,
                    session_key=appointment_id,
                )

            updated_text = (
                f"{NotificationsTexts.status_rejected()}\nПричина: {reason_text}\n\n{context.message_text or ''}"
            )
            return UnifiedViewDTO(
                content=self.ui.render_post_action(updated_text, appointment_id, context.message_thread_id),
                chat_id=self.settings.telegram_admin_channel_id,
                session_key=appointment_id,
                message_thread_id=context.message_thread_id,
                mode="edit",
                alert_text=NotificationsTexts.alert_rejected(),
            )
        except Exception as e:
            log.error(f"Orchestrator | Reject error: {e}")
            return UnifiedViewDTO(
                alert_text=NotificationsTexts.error_api(),
                chat_id=self.settings.telegram_admin_channel_id,
                session_key=appointment_id,
            )

    async def _handler_cancel_reject(self, context: QueryContext) -> UnifiedViewDTO:
        if context.session_id is None:
            return UnifiedViewDTO(alert_text="Ошибка: ID не найден")

        appointment_id = int(context.session_id)
        return UnifiedViewDTO(
            content=self.ui.render_main(context.message_text or "", appointment_id, context.message_thread_id),
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=appointment_id,
            message_thread_id=context.message_thread_id,
            mode="edit",
            alert_text=NotificationsTexts.alert_cancelled(),
        )

    async def _handler_delete_notification(self, context: QueryContext) -> UnifiedViewDTO:
        return UnifiedViewDTO(
            clean_history=True,
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=context.session_id,
            alert_text=NotificationsTexts.alert_deleted(),
        )

    async def handle_entry(self, user_id: int, chat_id: int | None = None, payload: Any = None) -> UnifiedViewDTO:
        """
        Точка входа.
        """
        return UnifiedViewDTO(alert_text="Фича уведомлений работает только через callback")

    async def render_content(self, payload: Any) -> Any:
        return None

import functools
from typing import TYPE_CHECKING, Any

from aiogram.types import CallbackQuery
from loguru import logger as log

from src.telegram_bot.core.api_client import BaseApiClient
from src.telegram_bot.services.base.base_orchestrator import BaseBotOrchestrator
from src.telegram_bot.services.base.view_dto import UnifiedViewDTO, ViewResultDTO

from ..contracts.contract import NotificationsDataProvider
from ..resources.callbacks import NotificationsCallback
from ..resources.dto import QueryContext
from ..resources.keyboards import build_contact_full_kb
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
        self.site_settings = container.site_settings
        self.url_signer = container.url_signer
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
            "read_contact": self._handler_read_contact,
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

            # Добавляем начальные статусы "Ожидание"
            updated_text = self.ui.append_statuses(updated_text, email_status="waiting", twilio_status="waiting")

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

    async def _handler_read_contact(self, context: QueryContext) -> UnifiedViewDTO:
        """Раскрывает превью контактной заявки — показывает полный текст + кнопки."""
        if context.session_id is None:
            return UnifiedViewDTO(alert_text="Ошибка: ID заявки не найден")

        # Пытаемся достать полный текст из кэша
        contact_cache = self.container.redis.contact_cache
        data = await contact_cache.get(context.session_id)

        full_text = data["text"] if data and "text" in data else NotificationsTexts.error_contact_not_found()

        # Формируем подписанную ссылку для TMA
        site_base_url = await self.site_settings.get_field("site_base_url") or "https://lily-salon.de"
        signed_url = self.url_signer.generate_signed_url(
            base_url=site_base_url, request_id=context.session_id, action="reply"
        )

        # Для контактов принудительно используем None для топика
        kb = build_contact_full_kb(
            request_id=context.session_id,
            signed_url=signed_url,
            topic_id=None,
        )

        return UnifiedViewDTO(
            content=ViewResultDTO(text=full_text, kb=kb),
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=f"contact_{context.session_id}",
            message_thread_id=None,
            mode="edit",
        )

    async def handle_status_update(
        self, payload: dict[str, Any], current_text: str | None = None
    ) -> UnifiedViewDTO | None:
        """
        Обработка обновления статуса отправки (из Redis Stream).
        Использует данные из AppointmentCache для восстановления текста.
        current_text здесь игнорируется, так как мы восстанавливаем его заново.
        """
        try:
            appointment_id = int(payload.get("appointment_id", 0)) or int(payload.get("confirmation_id", 0))
            channel = payload.get("channel")
            status = payload.get("status")

            if not appointment_id or not channel or not status:
                log.warning(f"Orchestrator | Invalid status update payload: {payload}")
                return None

            # 1. Загружаем данные заявки из кэша
            appointment_data = await self.container.redis.appointment_cache.get(appointment_id)
            if not appointment_data:
                log.warning(
                    f"Orchestrator | No cache found for appointment {appointment_id}. Cannot reconstruct message."
                )
                return None

            # 2. Восстанавливаем текст и добавляем статусы
            email_status = status if channel == "email" else "waiting"
            twilio_status = status if channel == "twilio" else "waiting"

            new_text = self.ui.reconstruct_message(
                appointment_data, email_status=email_status, twilio_status=twilio_status
            )

            return UnifiedViewDTO(
                content=self.ui.render_post_action(new_text, appointment_id),
                chat_id=self.settings.telegram_admin_channel_id,
                session_key=appointment_id,
                mode="edit",
            )
        except Exception as e:
            log.error(f"Orchestrator | handle_status_update error: {e}")
            return None

    async def handle_entry(self, user_id: int, chat_id: int | None = None, payload: Any = None) -> UnifiedViewDTO:
        """
        Точка входа.
        """
        return UnifiedViewDTO(
            alert_text="Фича уведомлений работает только через callback",
            chat_id=chat_id or user_id,
            session_key=user_id,
        )

    async def render_content(self, payload: Any) -> Any:
        return None

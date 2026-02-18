from typing import TYPE_CHECKING, Any

from loguru import logger as log

from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.services.base import UnifiedViewDTO, ViewResultDTO

from ..resources.dto import BookingNotificationPayload
from ..ui.ui import NotificationsUI

if TYPE_CHECKING:
    from src.telegram_bot.core.container import BotContainer


class NotificationsOrchestrator:
    """
    Оркестратор для фичи Notifications (Redis Stream events).
    """

    def __init__(self, settings: BotSettings, container: "BotContainer"):
        self.settings = settings
        self.container = container
        self.ui = NotificationsUI()

    def _get_target_topic(self, payload: BookingNotificationPayload) -> int | None:
        """Вычисляет ID топика на основе категории услуги."""
        message_thread_id = self.settings.telegram_notification_topic_id
        if payload.category_slug and self.settings.telegram_topics:
            topic_id = self.settings.telegram_topics.get(payload.category_slug)
            if topic_id:
                message_thread_id = topic_id
        return message_thread_id

    def handle_notification(self, raw_payload: dict[str, Any]) -> UnifiedViewDTO:
        """Обрабатывает входящее уведомление о новой записи."""
        try:
            payload = BookingNotificationPayload(**raw_payload)
        except Exception as e:
            log.error(f"NotificationsOrchestrator | Validation error: {e}")
            return self.handle_failure(raw_payload, str(e))

        message_thread_id = self._get_target_topic(payload)
        view_result = self.ui.render_notification(payload, topic_id=message_thread_id)

        return UnifiedViewDTO(
            content=view_result,
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=payload.id,
            mode="topic" if message_thread_id else "channel",
            message_thread_id=message_thread_id,
        )

    async def handle_status_update(self, message_data: dict[str, Any]) -> UnifiedViewDTO | None:
        """
        Обрабатывает обновление статуса (Email/SMS) от воркера.
        Сохраняет статусы в кэш, чтобы избежать гонки и корректно обновить UI.
        """
        appointment_id = message_data.get("appointment_id")
        if not appointment_id:
            return None

        # 1. Достаем текущие данные из кэша
        appointment_cache = await self.container.redis.appointment_cache.get(appointment_id)
        if not appointment_cache:
            log.warning(f"NotificationsOrchestrator | No cache for {appointment_id}.")
            return None

        # 2. Обновляем статус конкретного канала в данных кэша
        channel = message_data.get("channel")
        status = message_data.get("status")

        if channel == "email":
            appointment_cache["email_delivery_status"] = status
        elif channel == "twilio":
            appointment_cache["twilio_delivery_status"] = status

        # 3. Сохраняем обновленные данные обратно в кэш
        await self.container.redis.appointment_cache.save(appointment_id, appointment_cache)

        try:
            payload = BookingNotificationPayload(**appointment_cache)
        except Exception as e:
            log.error(f"NotificationsOrchestrator | Cache validation error: {e}")
            return None

        # 4. Вычисляем топик и получаем все статусы из кэша
        message_thread_id = self._get_target_topic(payload)
        email_status = appointment_cache.get("email_delivery_status", "waiting")
        twilio_status = appointment_cache.get("twilio_delivery_status", "waiting")

        # 5. Рендерим ПОЛНУЮ карточку заново с актуальными галочками
        view_result = self.ui.render_notification(
            payload, topic_id=message_thread_id, email_status=email_status, twilio_status=twilio_status
        )

        return UnifiedViewDTO(
            content=view_result,
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=appointment_id,
            mode="topic" if message_thread_id else "channel",
            message_thread_id=message_thread_id,
        )

    def handle_failure(self, raw_payload: dict[str, Any], error_msg: str) -> UnifiedViewDTO:
        booking_id = raw_payload.get("id", "???")
        text = f"⚠️ <b>Ошибка обработки уведомления #{booking_id}</b>\n<b>Ошибка:</b> {error_msg}"
        return UnifiedViewDTO(
            content=ViewResultDTO(text=text),
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=f"fail_{booking_id}",
            mode="topic",
            message_thread_id=self.settings.telegram_notification_topic_id,
        )

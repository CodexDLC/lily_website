from typing import Any

from loguru import logger as log

from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.services.base import UnifiedViewDTO, ViewResultDTO

from ..resources.dto import BookingNotificationPayload
from ..ui.ui import NotificationsUI


class NotificationsOrchestrator:
    """
    Оркестратор для фичи Notifications.
    """

    def __init__(self, settings: BotSettings):
        self.settings = settings
        self.ui = NotificationsUI()

    def handle_notification(self, raw_payload: dict[str, Any]) -> UnifiedViewDTO:
        """
        Обрабатывает входящее уведомление, валидируя его через Pydantic.
        """
        log.debug(f"NotificationsOrchestrator | Validating payload: {raw_payload}")

        try:
            payload = BookingNotificationPayload(**raw_payload)
        except Exception as e:
            log.error(f"NotificationsOrchestrator | Validation error: {e}")
            return self.handle_failure(raw_payload, str(e))

        target_chat_id = self.settings.telegram_admin_channel_id
        message_thread_id = self.settings.telegram_notification_topic_id

        if payload.category_slug and self.settings.telegram_topics:
            topic_id = self.settings.telegram_topics.get(payload.category_slug)
            if topic_id:
                message_thread_id = topic_id

        view_result = self.ui.render_notification(payload, topic_id=message_thread_id)

        return UnifiedViewDTO(
            content=view_result,
            chat_id=target_chat_id,
            session_key=payload.id,
            mode="topic" if message_thread_id else "channel",
            message_thread_id=message_thread_id,
        )

    async def handle_status_update(self, message_data: dict[str, Any]) -> UnifiedViewDTO | None:
        """
        Обрабатывает обновление статуса (Email/SMS) от воркера.
        """
        appointment_id = message_data.get("appointment_id")
        channel = message_data.get("channel", "unknown")
        status = message_data.get("status", "unknown")

        log.info(f"NotificationsOrchestrator | Status update: ID={appointment_id} channel={channel} status={status}")

        # Формируем текст уведомления для админов
        status_emoji = "✅" if status == "sent" or status == "success" else "❌"
        status_text = "отправлено" if status == "sent" or status == "success" else f"ошибка ({status})"

        text = (
            f"{status_emoji} <b>Уведомление клиенту (#{appointment_id})</b>\n"
            f"Канал: <code>{channel.upper()}</code>\n"
            f"Статус: <b>{status_text}</b>"
        )

        # Важно: передаем message_thread_id, чтобы сообщение попало в нужный топик
        return UnifiedViewDTO(
            content=ViewResultDTO(text=text),
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=f"status_{appointment_id}_{channel}",
            mode="topic",
            message_thread_id=self.settings.telegram_notification_topic_id,
        )

    def handle_failure(self, raw_payload: dict[str, Any], error_msg: str) -> UnifiedViewDTO:
        booking_id = raw_payload.get("id", "???")
        text = (
            f"⚠️ <b>Ошибка обработки уведомления</b>\n\n"
            f"Поступила новая запись <b>#{booking_id}</b>, но бот не смог обработать данные.\n"
            f"<b>Ошибка:</b> <code>{error_msg}</code>"
        )
        return UnifiedViewDTO(
            content=ViewResultDTO(text=text),
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=f"fail_{booking_id}",
            mode="topic",
            message_thread_id=self.settings.telegram_notification_topic_id,
        )

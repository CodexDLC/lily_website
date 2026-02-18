from typing import Any

from src.telegram_bot.features.redis.notifications.resources.dto import BookingNotificationPayload
from src.telegram_bot.features.redis.notifications.resources.formatters import format_new_booking
from src.telegram_bot.features.telegram.notifications.resources.formatters import NotificationsFormatter
from src.telegram_bot.features.telegram.notifications.resources.keyboards import (
    build_main_kb,
    build_post_action_kb,
    build_reject_reasons_kb,
)
from src.telegram_bot.features.telegram.notifications.resources.texts import NotificationsTexts
from src.telegram_bot.services.base.view_dto import ViewResultDTO


class NotificationsUI:
    """
    UI сервис для фичи Notifications.
    """

    def __init__(self):
        self.formatter = NotificationsFormatter()

    def render_main(self, text: str, appointment_id: int, topic_id: int | None = None) -> ViewResultDTO:
        """Отрисовка основного экрана управления."""
        kb = build_main_kb(appointment_id=appointment_id, topic_id=topic_id)
        return ViewResultDTO(text=text, kb=kb)

    def render_reject_reasons(self, appointment_id: int, topic_id: int | None = None) -> ViewResultDTO:
        """Отрисовка меню выбора причин отклонения."""
        return ViewResultDTO(
            text=NotificationsTexts.prompt_select_reason(),
            kb=build_reject_reasons_kb(appointment_id=appointment_id, topic_id=topic_id),
        )

    def render_post_action(self, text: str, appointment_id: int, topic_id: int | None = None) -> ViewResultDTO:
        """Отрисовка экрана после выполнения действия."""
        kb = build_post_action_kb(appointment_id=appointment_id, topic_id=topic_id)
        return ViewResultDTO(text=text, kb=kb)

    def render_email_data(
        self, appointment_data: dict[str, Any], status: str, reason_text: str | None = None
    ) -> dict[str, Any]:
        return self.formatter.prepare_email_data(appointment_data, status, reason_text)

    def append_statuses(self, text: str, email_status: str | None = None, twilio_status: str | None = None) -> str:
        """
        Добавляет или обновляет статусы отправки в тексте сообщения.
        Статусы: "waiting" (⏳), "success" (✅), "failed" (❌).
        """
        status_lines = []
        if email_status:
            icon = "⏳" if email_status == "waiting" else "✅" if email_status == "success" else "❌"
            status_lines.append(f"Email: {icon}")

        if twilio_status:
            icon = "⏳" if twilio_status == "waiting" else "✅" if twilio_status == "success" else "❌"
            status_lines.append(f"SMS/WhatsApp: {icon}")

        if not status_lines:
            return text

        return text + "\n\n" + "\n".join(status_lines)

    def reconstruct_message(
        self, appointment_data: dict[str, Any], email_status: str | None = None, twilio_status: str | None = None
    ) -> str:
        """
        Восстанавливает текст сообщения из данных заявки и добавляет статусы.
        """
        try:
            payload = BookingNotificationPayload(**appointment_data)
            base_text = format_new_booking(payload)

            # Добавляем заголовок "Подтверждено"
            base_text = f"{NotificationsTexts.status_approved()}\n\n{base_text}"

        except Exception:
            # Fallback
            base_text = f"Заявка #{appointment_data.get('id', '???')}"

        return self.append_statuses(base_text, email_status, twilio_status)

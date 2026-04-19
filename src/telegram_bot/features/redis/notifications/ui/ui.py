from src.telegram_bot.services.base import ViewResultDTO

from ..resources.dto import BookingNotificationPayload
from ..resources.formatters import format_new_booking
from ..resources.keyboards import build_main_kb, build_post_action_kb


class NotificationsUI:
    """
    UI сервис для фичи Notifications.
    """

    def render_notification(
        self,
        payload: BookingNotificationPayload,
        topic_id: int | None = None,
        email_status: str = "none",
        twilio_status: str = "none",
        email_label: str = "",
        twilio_label: str = "",
        base_url: str = "https://lily-salon.de",
    ) -> ViewResultDTO:
        """Рендерит полную карточку записи со статусами."""
        text = format_new_booking(
            payload,
            email_status=email_status,
            twilio_status=twilio_status,
            email_label=email_label,
            twilio_label=twilio_label,
        )

        # Если статусы уже пошли, показываем кнопку "Удалить" вместо "Подтвердить/Отклонить"
        if email_status != "none" or twilio_status != "none":
            kb = build_post_action_kb(payload.id, topic_id=topic_id)
        else:
            kb = build_main_kb(payload.id, topic_id=topic_id, base_url=base_url)

        return ViewResultDTO(text=text, kb=kb)

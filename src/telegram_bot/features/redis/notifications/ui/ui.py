from src.telegram_bot.services.base import ViewResultDTO

from ..resources.dto import BookingNotificationPayload
from ..resources.formatters import format_new_booking
from ..resources.keyboards import build_main_kb


class NotificationsUI:
    """
    UI сервис для фичи Notifications.
    """

    def render_notification(self, payload: BookingNotificationPayload) -> ViewResultDTO:
        text = format_new_booking(payload)
        kb = build_main_kb(payload.id)

        return ViewResultDTO(text=text, kb=kb)

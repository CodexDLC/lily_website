from typing import TYPE_CHECKING, Any

from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.services.base import UnifiedViewDTO

from .booking_processor import BookingProcessor
from .contact_processor import ContactProcessor

if TYPE_CHECKING:
    from src.telegram_bot.core.container import BotContainer


class NotificationsOrchestrator:
    """
    Оркестратор для фичи Notifications (Redis Stream events).
    Тонкий маршрутизатор — делегирует работу процессорам.
    """

    def __init__(self, settings: BotSettings, container: "BotContainer"):
        self.settings = settings
        self.container = container
        self.booking = BookingProcessor(settings, container)
        self.contact = ContactProcessor(settings, container)

    # --- Booking ---

    def handle_notification(self, raw_payload: dict[str, Any]) -> UnifiedViewDTO:
        """Делегирует обработку уведомления о бронировании."""
        return self.booking.handle_notification(raw_payload)

    async def handle_status_update(self, message_data: dict[str, Any]) -> UnifiedViewDTO | None:
        """Делегирует обновление статуса бронирования."""
        return await self.booking.handle_status_update(message_data)

    def handle_failure(self, raw_payload: dict[str, Any], error_msg: str) -> UnifiedViewDTO:
        """Делегирует обработку ошибки бронирования."""
        return self.booking.handle_failure(raw_payload, error_msg)

    # --- Contact ---

    async def handle_contact_notification(self, raw_payload: dict[str, Any]) -> UnifiedViewDTO:
        """Делегирует обработку уведомления из контактной формы."""
        return await self.contact.handle_notification(raw_payload)

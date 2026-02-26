from typing import TYPE_CHECKING, Any

from loguru import logger

from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.services.base import UnifiedViewDTO

from ..contracts.contract import AppointmentsDataProvider
from .booking_processor import BookingProcessor
from .contact_processor import ContactProcessor

if TYPE_CHECKING:
    from src.telegram_bot.core.container import BotContainer


class NotificationsOrchestrator:
    """
    Orchestrator for the Notifications feature (Redis Stream events).
    Thin router — delegates work to processors.
    """

    def __init__(
        self,
        settings: BotSettings,
        container: "BotContainer",
        appointments_provider: AppointmentsDataProvider | None = None,
    ):
        self.settings = settings
        self.container = container
        self.appointments_provider = appointments_provider

        self.booking = BookingProcessor(settings, container, appointments_provider)
        self.contact = ContactProcessor(settings, container)

    # --- Booking ---

    def handle_notification(self, raw_payload: dict[str, Any]) -> UnifiedViewDTO:
        """Delegates booking notification processing."""
        logger.debug(f"Bot: NotificationsOrchestrator | Action: HandleBooking | payload={raw_payload}")
        return self.booking.handle_notification(raw_payload)

    async def handle_status_update(self, message_data: dict[str, Any]) -> UnifiedViewDTO | None:
        """Delegates booking status update."""
        logger.debug(f"Bot: NotificationsOrchestrator | Action: HandleStatusUpdate | data={message_data}")
        return await self.booking.handle_status_update(message_data)

    def handle_failure(self, raw_payload: dict[str, Any], error_msg: str) -> UnifiedViewDTO:
        """Delegates booking failure processing."""
        logger.error(
            f"Bot: NotificationsOrchestrator | Action: HandleFailure | error={error_msg} | payload={raw_payload}"
        )
        return self.booking.handle_failure(raw_payload, error_msg)

    async def handle_expire_reschedule(self, message_data: dict[str, Any]) -> None:
        """Delegates reschedule expiration processing."""
        logger.info(f"Bot: NotificationsOrchestrator | Action: HandleExpireReschedule | data={message_data}")
        return await self.booking.handle_expire_reschedule(message_data)

    # --- Contact ---

    async def handle_contact_notification(self, raw_payload: dict[str, Any]) -> UnifiedViewDTO:
        """Delegates contact form notification processing."""
        logger.debug(f"Bot: NotificationsOrchestrator | Action: HandleContact | payload={raw_payload}")
        return await self.contact.handle_notification(raw_payload)

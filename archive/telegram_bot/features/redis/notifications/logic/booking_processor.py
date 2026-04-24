from typing import TYPE_CHECKING, Any, cast

from aiogram_i18n import I18nContext
from codex_bot.base import UnifiedViewDTO, ViewResultDTO
from loguru import logger as log

from src.telegram_bot.core.config import BotSettings

from ..contracts.contract import AppointmentsDataProvider
from ..resources.dto import BookingNotificationPayload
from ..ui.ui import NotificationsUI

if TYPE_CHECKING:
    from src.telegram_bot.core.container import BotContainer


class BookingProcessor:
    """
    Processor for handling booking notifications.
    Separated from NotificationsOrchestrator for better responsibility division.
    """

    def __init__(
        self,
        settings: BotSettings,
        container: "BotContainer",
        appointments_provider: AppointmentsDataProvider | None = None,
    ):
        self.settings = settings
        self.container = container
        self.ui = NotificationsUI()
        self.appointments_provider = appointments_provider

    def _get_target_topic(self, payload: BookingNotificationPayload) -> int | None:
        """Returns the configured topic ID for booking notifications."""
        if self.settings.telegram_topics:
            topic_id = self.settings.telegram_topics.get("termin")
            if topic_id:
                return topic_id
        return self.settings.telegram_notification_topic_id

    async def handle_notification(self, raw_payload: dict[str, Any]) -> UnifiedViewDTO:
        """Processes incoming notification about a new booking."""
        log.debug(f"Bot: BookingProcessor | Action: HandleNotification | appt_id={raw_payload.get('id')}")
        try:
            payload = BookingNotificationPayload(**raw_payload)
        except Exception as e:
            log.error(f"Bot: BookingProcessor | Action: ValidationFailed | error={e} | payload={raw_payload}")
            return await self.handle_failure(raw_payload, str(e))

        # Get base URL from site settings
        base_url = await self.container.site_settings.aget_field("site_base_url") or "https://lily-salon.de"

        message_thread_id = self._get_target_topic(payload)
        view_result = self.ui.render_notification(payload, topic_id=message_thread_id, base_url=base_url)

        log.info(f"Bot: BookingProcessor | Action: Success | appt_id={payload.id} | topic={message_thread_id}")
        return UnifiedViewDTO(
            content=view_result,
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=payload.id,
            mode="topic" if message_thread_id else "channel",
            message_thread_id=message_thread_id,
        )

    async def handle_status_update(self, message_data: dict[str, Any]) -> UnifiedViewDTO | None:
        """
        Handles status updates (Email/SMS) from the worker.
        Saves statuses to cache to avoid race conditions and correctly update UI.
        """
        appointment_id = message_data.get("appointment_id")
        channel = message_data.get("channel")
        status = message_data.get("status")
        notification_label = message_data.get("notification_label") or ""
        event_type = message_data.get("event_type") or ""
        template_name = message_data.get("template_name") or ""

        log.debug(
            f"Bot: BookingProcessor | Action: StatusUpdate | appt_id={appointment_id} | channel={channel} | status={status}"
        )

        if not appointment_id:
            log.warning("Bot: BookingProcessor | Action: StatusUpdate | error=NoAppointmentID")
            return None

        # 1. Get current data from cache
        appointment_cache = await self.container.redis.appointment_cache.get(appointment_id)
        if not appointment_cache:
            log.warning(f"Bot: BookingProcessor | Action: StatusUpdate | error=NoCacheFound | appt_id={appointment_id}")
            return None

        # 2. Update specific channel status in cache data
        if channel == "email":
            appointment_cache["email_delivery_status"] = status
            if notification_label:
                appointment_cache["email_notification_label"] = notification_label
            if event_type:
                appointment_cache["last_email_event_type"] = event_type
            if template_name:
                appointment_cache["last_email_template_name"] = template_name
        elif channel == "twilio":
            appointment_cache["twilio_delivery_status"] = status
            if notification_label:
                appointment_cache["twilio_notification_label"] = notification_label

        # 3. Save updated data back to cache
        await self.container.redis.appointment_cache.save(appointment_id, appointment_cache)

        try:
            payload = BookingNotificationPayload(**appointment_cache)
        except Exception as e:
            log.error(f"Bot: BookingProcessor | Action: CacheValidationFailed | appt_id={appointment_id} | error={e}")
            return None

        # 4. Calculate topic and get all statuses from cache
        message_thread_id = self._get_target_topic(payload)
        email_status = appointment_cache.get("email_delivery_status", "waiting")
        twilio_status = appointment_cache.get("twilio_delivery_status", "waiting")
        email_label = appointment_cache.get("email_notification_label", "")
        twilio_label = appointment_cache.get("twilio_notification_label", "")

        # Get base URL from site settings
        base_url = await self.container.site_settings.aget_field("site_base_url") or "https://lily-salon.de"

        # 5. Re-render FULL card with actual status icons
        view_result = self.ui.render_notification(
            payload,
            topic_id=message_thread_id,
            email_status=email_status,
            twilio_status=twilio_status,
            email_label=email_label,
            twilio_label=twilio_label,
            base_url=base_url,
        )

        log.info(
            f"Bot: BookingProcessor | Action: UIUpdated | appt_id={appointment_id} | email={email_status} | twilio={twilio_status}"
        )
        return UnifiedViewDTO(
            content=view_result,
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=appointment_id,
            mode="topic" if message_thread_id else "channel",
            message_thread_id=message_thread_id,
        )

    async def handle_failure(self, raw_payload: dict[str, Any], error_msg: str) -> UnifiedViewDTO:
        i18n = cast("I18nContext", I18nContext.get_current())
        booking_id = raw_payload.get("id", "???")
        log.error(f"Bot: BookingProcessor | Action: FailureHandled | appt_id={booking_id} | error={error_msg}")

        text = i18n.notifications.error.api(booking_id=booking_id, error=error_msg)
        return UnifiedViewDTO(
            content=ViewResultDTO(text=text),
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=f"fail_{booking_id}",
            mode="topic",
            message_thread_id=self.settings.telegram_notification_topic_id,
        )

    async def handle_expire_reschedule(self, raw_payload: dict[str, Any]) -> None:
        """
        Logic for handling expired reschedule time.
        Sends API request to Django to cancel the pending booking.
        """
        appointment_id = raw_payload.get("appointment_id")
        log.info(f"Bot: BookingProcessor | Action: ExpireReschedule | appt_id={appointment_id}")

        if not appointment_id:
            log.warning("Bot: BookingProcessor | Action: ExpireReschedule | error=NoAppointmentID")
            return

        if not self.appointments_provider:
            log.error("Bot: BookingProcessor | Action: ExpireReschedule | error=ProviderNotFound")
            return

        try:
            # Send expiration command to Django API
            response = await self.appointments_provider.expire_reschedule(appointment_id)
            log.info(f"Bot: BookingProcessor | Action: ExpireSuccess | appt_id={appointment_id} | response={response}")
        except Exception as e:
            log.error(f"Bot: BookingProcessor | Action: ExpireFailed | appt_id={appointment_id} | error={e}")
            raise

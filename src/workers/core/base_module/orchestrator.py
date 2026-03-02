from typing import TYPE_CHECKING

from loguru import logger as log

if TYPE_CHECKING:
    from .email_client import AsyncEmailClient
    from .seven_io_client import SevenIOClient
    from .twilio_service import TwilioService


class NotificationOrchestrator:
    """
    Tiered Notification Orchestrator.
    Handles fallbacks between different providers.
    """

    def __init__(
        self,
        email_client: "AsyncEmailClient",
        seven_io_client: "SevenIOClient",
        twilio_client: "TwilioService",
    ):
        self.email_client = email_client
        self.seven_io_client = seven_io_client
        self.twilio_client = twilio_client

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str | None = None,
        timeout: int = 15,
    ) -> bool:
        """
        Sends email with fallback: SMTP -> SendGrid (via Twilio).
        """
        # 1. Primary: SMTP
        try:
            log.info(f"Orchestrator | Action: SendEmail | Step: Primary | to={to_email}")
            await self.email_client.send_email(to_email, subject, html_content, timeout=timeout)
            return True
        except Exception as e:
            log.warning(f"Orchestrator | Action: SendEmail | Step: PrimaryFailed | error={e}")

        # 2. Fallback: SendGrid (via Twilio)
        from typing import cast

        sender = cast("str", from_email or self.email_client.smtp_from_email)
        log.info(f"Orchestrator | Action: SendEmail | Step: Fallback | to={to_email}")
        return await self.twilio_client.send_email(to_email, subject, html_content, from_email=sender, timeout=timeout)

    async def send_message(
        self,
        to_number: str,
        text: str,
        media_url: str | None = None,
        wa_template_sid: str | None = None,
        wa_variables: dict | None = None,
    ) -> bool:
        """
        Sends message with tiered fallback:
        SevenIO (WA -> SMS) -> Twilio (WA -> SMS)
        """
        log.info(f"Orchestrator | Action: SendMessage | to={to_number}")

        # --- STEP 1: Seven.io ---
        # 1.1 WhatsApp
        log.debug("Orchestrator | Action: SendMessage | Provider: SevenIO | Mode: WhatsApp")
        success = await self.seven_io_client.send_whatsapp(to_number, text)
        if success:
            return True

        # 1.2 SMS fallback within Seven.io
        log.warning("Orchestrator | Action: SendMessage | Provider: SevenIO | Mode: SMS Fallback")
        success = await self.seven_io_client.send_sms(to_number, text)
        if success:
            return True

        # --- STEP 2: Twilio (Final Reserve) ---
        # 2.1 WhatsApp (Template if available, else Free-form)
        log.info("Orchestrator | Action: SendMessage | Provider: Twilio | Mode: WhatsApp Fallback")
        if wa_template_sid and wa_variables:
            success = self.twilio_client.send_whatsapp_template(to_number, wa_template_sid, wa_variables)
        else:
            success = self.twilio_client.send_whatsapp(to_number, text, media_url=media_url)

        if success:
            return True

        # 2.2 SMS (The last resort)
        log.warning("Orchestrator | Action: SendMessage | Provider: Twilio | Mode: SMS LastResort")
        return self.twilio_client.send_sms(to_number, text)

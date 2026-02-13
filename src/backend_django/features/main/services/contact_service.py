from typing import cast

from core.arq.client import DjangoArqClient
from django.conf import settings
from features.booking.services.client_service import ClientService

from ..models import ContactRequest


class ContactService:
    """Service for handling contact form submissions."""

    @staticmethod
    def create_request(
        first_name: str,
        last_name: str,
        contact_type: str,
        contact_value: str,
        message: str,
        topic: str = "general",
        consent_marketing: bool = False,
    ) -> ContactRequest:
        """
        Creates a ContactRequest linked to a Client.
        """
        phone = ""
        email = ""

        if contact_type == "email":
            email = contact_value
        else:
            phone = contact_value

        # 1. Get or Create Client
        client = ClientService.get_or_create_client(
            first_name=first_name, last_name=last_name, phone=phone, email=email, consent_marketing=consent_marketing
        )

        # 2. Create Request
        request = cast("ContactRequest", ContactRequest.objects.create(client=client, message=message, topic=topic))

        # 3. Send Notification via ARQ (Telegram Bot)
        admin_chat_id = getattr(settings, "TELEGRAM_ADMIN_ID", None)

        if admin_chat_id:
            # Formatted text for the message
            text = (
                f"📋 <b>Neue Anfrage von Website</b>\n\n"
                f"👤 <b>{first_name} {last_name}</b>\n"
                f"📞 {contact_value} ({contact_type})\n"
                f"🎯 <b>Thema:</b> {request.get_topic_display()}\n"
                f"💬 {message}"
            )

            # We pass request_id so the 02_telegram_bot can attach Inline Buttons (Confirm/Cancel)
            DjangoArqClient.enqueue_job(
                "send_notification_task",
                user_id=int(admin_chat_id),
                message=text,
                request_id=request.id,  # <--- Added ID
            )

        return request

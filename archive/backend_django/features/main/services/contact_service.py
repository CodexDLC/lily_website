from typing import cast

from core.logger import log
from features.booking.services.utils.client_service import ClientService
from features.system.services.notification import NotificationService

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
        lang: str = "de",  # Default to German
    ) -> ContactRequest:
        """
        Creates a ContactRequest linked to a Client and triggers notifications.
        """
        log.debug(
            f"Creating contact request: {first_name} {last_name}, type={contact_type}, "
            f"value={contact_value}, topic={topic}, lang={lang}"
        )

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
        log.info(f"ContactRequest created: ID={request.id} for Client={client.id}")

        # 3. Trigger Universal Notification with language support
        try:
            NotificationService.send_contact_receipt(
                recipient_email=client.email,
                client_name=client.first_name,
                message_text=message,
                request_id=request.id,
                lang=lang,  # Pass language to notification service
            )
            log.info(f"Notifications triggered for request {request.id}")
        except Exception as e:
            log.error(f"Failed to trigger notifications for request {request.id}: {e}")

        return request

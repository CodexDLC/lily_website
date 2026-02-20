from contextlib import suppress
from typing import cast

from core.arq.client import DjangoArqClient
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

        # 3. Seed Redis Cache & Send Notification via ARQ
        from features.system.redis_managers.notification_cache_manager import NotificationCacheManager

        # Seed the rich metadata to Redis for the Bot
        NotificationCacheManager.seed_contact_request(request.id)

        # Suppress exceptions to not fail the request creation
        with suppress(Exception):
            DjangoArqClient.enqueue_job(
                "send_contact_notification_task",
                request_id=request.id,
                # Note: 'message' is removed here, Worker must fetch from Redis
            )

        return request

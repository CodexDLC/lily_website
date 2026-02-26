from typing import cast

from core.arq.client import DjangoArqClient
from core.logger import log
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
        log.debug(
            f"Creating contact request: {first_name} {last_name}, type={contact_type}, "
            f"value={contact_value}, topic={topic}"
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
        log.debug(f"Client resolved: ID={client.id}")

        # 2. Create Request
        request = cast("ContactRequest", ContactRequest.objects.create(client=client, message=message, topic=topic))
        log.info(f"ContactRequest created: ID={request.id} for Client={client.id}")

        # 3. Seed Redis Cache & Send Notification via ARQ
        from features.system.redis_managers.notification_cache_manager import NotificationCacheManager

        try:
            # Seed the rich metadata to Redis for the Bot
            NotificationCacheManager.seed_contact_request(request.id)
            log.debug(f"Seeded contact request {request.id} to Redis")

            log.debug(f"Enqueuing notification task for request {request.id}")
            DjangoArqClient.enqueue_job(
                "send_contact_notification_task",
                request_id=request.id,
            )
            log.info(f"Successfully enqueued notification for request {request.id}")
        except Exception as e:
            # We don't want to fail the whole request creation if notification fails
            log.error(f"Failed to process post-creation tasks for request {request.id}: {e}")

        return request

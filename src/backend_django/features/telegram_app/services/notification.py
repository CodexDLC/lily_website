import logging

from core.arq.client import DjangoArqClient
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class NotificationService:
    """Service to handle Telegram App notifications and queues."""

    @staticmethod
    def enqueue_reply_email(
        request_id: str, recipient_email: str, reply_text: str, subject: str = "Re: Your Request"
    ) -> bool:
        """
        Enqueues a task in ARQ to send the reply email directly, avoiding DB access in the worker.
        """
        try:
            DjangoArqClient.enqueue_job(
                "send_email_task",
                recipient_email=recipient_email,
                subject=subject,
                template_name="reply_to_client.html",
                data={"request_id": request_id, "reply_text": reply_text},
            )
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue reply email for request {request_id}: {e}")
            return False

    @staticmethod
    def enqueue_receipt_email(recipient_email: str, client_name: str, message_text: str) -> bool:
        """
        Enqueues an automatic receipt confirmation email to the client, translating text to the current active language.
        """
        try:
            subject = _("Wir haben Ihre Anfrage erhalten | LILY Beauty")
            DjangoArqClient.enqueue_job(
                "send_email_task",
                recipient_email=recipient_email,
                subject=subject,
                template_name="receipt_to_client.html",
                data={
                    "client_name": client_name,
                    "message_text": message_text,
                    "header_text": _("Wir haben Ihre Anfrage erhalten!"),
                    "greeting": _("Hallo"),
                    "body_text": _(
                        "Vielen Dank für Ihre Nachricht an LILY Beauty Salon. Wir haben Ihre Anfrage erfolgreich erhalten und werden uns so schnell wie möglich bei Ihnen melden."
                    ),
                    "quoted_message_label": _("Ihre Nachricht"),
                    "contact_hint": _(
                        "Falls Sie dringende Fragen haben, können Sie uns auch unter <strong>+49 176 59423704</strong> erreichen."
                    ),
                    "signature": _("Mit freundlichen Grüßen,\nIhr LILY Beauty Team"),
                },
            )
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue receipt email for {recipient_email}: {e}")
            return False

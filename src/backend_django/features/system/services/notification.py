from core.arq.client import DjangoArqClient
from core.logger import log
from django.utils.translation import gettext as _


class NotificationService:
    """Service to handle notifications and queues (Email, etc.)."""

    @staticmethod
    def enqueue_reply_email(
        request_id: str, recipient_email: str, reply_text: str, subject: str = "Re: Your Request"
    ) -> bool:
        """
        Enqueues a task in ARQ to send the reply email directly.
        """
        log.debug(
            f"Service: NotificationService | Action: EnqueueReply | request_id={request_id} | recipient={recipient_email}"
        )
        try:
            DjangoArqClient.enqueue_job(
                "send_email_task",
                recipient_email=recipient_email,
                subject=subject,
                template_name="reply_to_client.html",
                data={"request_id": request_id, "reply_text": reply_text},
            )
            log.info(f"Service: NotificationService | Action: Success | request_id={request_id}")
            return True
        except Exception as e:
            log.error(f"Service: NotificationService | Action: Failed | request_id={request_id} | error={e}")
            return False

    @staticmethod
    def enqueue_receipt_email(recipient_email: str, client_name: str, message_text: str) -> bool:
        """
        Enqueues an automatic receipt confirmation email to the client.
        """
        log.debug(
            f"Service: NotificationService | Action: EnqueueReceipt | recipient={recipient_email} | client={client_name}"
        )
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
            log.info(f"Service: NotificationService | Action: Success | recipient={recipient_email}")
            return True
        except Exception as e:
            log.error(f"Service: NotificationService | Action: Failed | recipient={recipient_email} | error={e}")
            return False

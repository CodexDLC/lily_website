import logging

from core.arq.client import DjangoArqClient

logger = logging.getLogger(__name__)


class NotificationService:
    """Service to handle Telegram App notifications and queues."""

    @staticmethod
    def enqueue_reply_email(request_id: str, reply_text: str, subject: str | None = None) -> bool:
        """
        Enqueues a task in ARQ to send the reply email.
        """
        try:
            # We enqueue the job so the worker can fetch the client email
            # based on request_id and send the email with reply_text.
            # The worker will also be responsible for publishing the Redis event
            # back to the bot.
            DjangoArqClient.enqueue_job(
                "send_tma_reply_email_task",
                request_id=request_id,
                reply_text=reply_text,
                subject=subject,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue reply email for request {request_id}: {e}")
            return False

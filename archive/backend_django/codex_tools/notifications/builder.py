"""
codex_tools.notifications.builder
==================================
Standardization of data for notifications.

Responsible for creating a unified dictionary (payload) that the
Notification Worker understands. Guarantees the presence of all required
fields: notification ID, recipient data, communication channels, and context.
"""

import uuid


class NotificationPayloadBuilder:
    """
    Builder of the universal data package for notifications.

    Used on the Django side to prepare a task for the queue.
    """

    @staticmethod
    def build(
        recipient_email: str | None = None,
        recipient_phone: str | None = None,
        first_name: str = "Guest",
        last_name: str = "",
        template_name: str | None = None,
        event_type: str | None = None,
        subject: str | None = None,
        context_data: dict | None = None,
        channels: list[str] | None = None,
        notification_id: str | None = None,
    ) -> dict:
        """
        Creates a valid dictionary for the send_universal_notification_task.

        Args:
            recipient_email: Recipient's email (for the email channel).
            recipient_phone: Recipient's phone (for sms/whatsapp channel).
            first_name: Recipient's first name for greeting.
            last_name: Recipient's last name.
            template_name: Short name of the template (e.g., 'ct_receipt').
            event_type: Event type for the Telegram bot (e.g., 'new_request').
            subject: Email subject (optional).
            context_data: Data dictionary for template rendering.
            channels: List of active channels ['email', 'telegram', 'sms'].
            notification_id: Unique UUID for tracking (generated if empty).

        Returns:
            dict: Standardized payload.
        """
        return {
            "notification_id": notification_id or str(uuid.uuid4()),
            "recipient": {
                "email": recipient_email,
                "phone": recipient_phone,
                "first_name": first_name,
                "last_name": last_name,
            },
            "template_name": template_name,
            "event_type": event_type,
            "subject": subject,
            "context_data": context_data or {},
            "channels": channels or ["email", "telegram"],
        }

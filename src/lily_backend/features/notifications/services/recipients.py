from django.conf import settings

from ..models import NotificationRecipient


def get_admin_notification_emails(kind: str = NotificationRecipient.KIND_ADMIN) -> list[str]:
    """
    Get a list of emails to receive admin notifications.
    Uses NotificationRecipient if any exist, otherwise falls back to settings.ADMINS.
    """
    qs = NotificationRecipient.objects.filter(kind=kind, enabled=True)
    if qs.exists():
        return list(qs.values_list("email", flat=True))

    # Fallback to ADMINS
    return [email for _, email in getattr(settings, "ADMINS", [])]

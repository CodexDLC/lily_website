from typing import Any

from django.core.signing import TimestampSigner
from django.urls import reverse


def build_admin_booking_context(appt_or_group: Any, recipient_email: str) -> dict[str, Any]:
    """
    Build context for an admin booking email.
    Includes a signed magic link to automatically log the admin in and open the booking.
    """
    is_group = hasattr(appt_or_group, "items")
    is_group = hasattr(appt_or_group, "items")

    from .notifications import build_booking_group_notification_context, build_booking_notification_context

    if is_group:
        context = build_booking_group_notification_context(appt_or_group)
        client = appt_or_group.client
        context["client_notes"] = ""  # Groups typically don't have aggregated notes currently
        target_path = reverse("cabinet:booking_schedule")  # fallback for group
    else:
        context = build_booking_notification_context(appt_or_group)
        client = appt_or_group.client
        context["client_phone"] = getattr(client, "phone", "") if client else ""
        context["client_email"] = getattr(client, "email", "") if client else ""
        context["client_notes"] = getattr(appt_or_group, "client_notes", "")
        # Link to the specific appointment modal in cabinet
        target_path = reverse("cabinet:booking_schedule") + f"?appointment={appt_or_group.pk}"

    # Generate magic login token for this specific admin email
    signer = TimestampSigner()
    token = signer.sign(recipient_email)

    from .notifications import _inject_site_context

    _inject_site_context(context)

    # Use site_url from context for the action link base
    site_url = context.get("site_url", "http://localhost:8000")
    magic_login_path = reverse("cabinet:magic_login")

    import urllib.parse

    query_string = urllib.parse.urlencode({"token": token, "target": target_path})

    context["action_url"] = f"{site_url}{magic_login_path}?{query_string}"
    return context

from __future__ import annotations

import base64

from django.conf import settings
from django.urls import reverse

# Importing the style moved to the feature directory
from features.booking.qr_style import qr_style


class AppointmentQRService:
    """Service to handle QR code generation for appointments."""

    @staticmethod
    def get_finalize_url(appointment) -> str:
        """Returns the absolute URL for the admin to adjust price."""
        path = reverse("cabinet:edit_price", kwargs={"token": appointment.finalize_token})
        # Note: In production SITE_URL should be set in settings.
        # For local dev, it might be http://127.0.0.1:8000
        site_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
        return f"{site_url}{path}"

    @classmethod
    def get_qr_base64(cls, appointment) -> str:
        """Returns the QR code as a base64 string for embedding in HTML."""
        url = cls.get_finalize_url(appointment)
        qr_bytes = qr_style.to_bytes(url, fmt="webp")
        return base64.b64encode(qr_bytes).decode("utf-8")

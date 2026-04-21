import os
import sys
from unittest.mock import MagicMock, patch

import django

# Setup Django
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), "src", "lily_backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.test")
django.setup()

from django.contrib.auth.models import AnonymousUser  # noqa: E402
from django.test import RequestFactory  # noqa: E402
from django.urls import reverse  # noqa: E402
from features.booking.views.public.commit import BookingCommitView  # noqa: E402
from features.booking.views.public.wizard import BookingWizardView  # noqa: E402


def debug_wizard():
    print("\n--- Debugging Wizard View ---")
    rf = RequestFactory()
    request = rf.get(reverse("booking:booking_wizard"))
    request.user = AnonymousUser()

    mock_cart = MagicMock()
    mock_cart.service_ids.return_value = []
    mock_cart.has.return_value = False

    with (
        patch("features.booking.views.public.wizard.get_cart", return_value=mock_cart),
        patch("features.booking.views.public.wizard.get_booking_project_data_provider") as mock_dp_func,
    ):
        mock_provider = MagicMock()
        mock_provider.get_public_services.return_value = [
            {
                "id": 1,
                "slug": "test-service",
                "title": "EXPECTED_SERVICE_TITLE",
                "duration": 60,
                "price": "100.00",
                "category_slug": "cat",
                "category_name": "Category",
            }
        ]
        mock_dp_func.return_value = mock_provider

        view = BookingWizardView.as_view()
        response = view(request)
        content = response.content.decode()

        if "EXPECTED_SERVICE_TITLE" in content:
            print("Wizard: Title found!")
        else:
            print("Wizard: Title NOT found in content.")
            print("Content Preview:", content[:1000])


def debug_commit():
    print("\n--- Debugging Commit View ---")
    rf = RequestFactory()
    # Sending empty post which should trigger validation error if not careful
    request = rf.post(reverse("booking:commit"), data={})
    request.user = AnonymousUser()
    from django.contrib.messages.storage.cookie import CookieStorage

    request._messages = CookieStorage(request)
    request.session = {}

    mock_cart = MagicMock()
    mock_cart.is_empty.return_value = False
    mock_cart.mode = "same_day"
    mock_cart.is_ready_same_day.return_value = True
    # Ensure contact is a real dict with strings, not mocks
    mock_cart.contact = {
        "first_name": "Test",
        "last_name": "User",
        "phone": "+49123456789",
        "email": "test@example.com",
    }

    with (
        patch("features.booking.selector.engine.get_booking_engine_gateway") as mock_engine_func,
        patch("features.conversations.services.notifications._get_engine"),
        patch("features.booking.views.public.commit.clear_cart"),
        patch("features.booking.views.public.commit.get_cart", return_value=mock_cart),
        patch("features.booking.views.public.commit.save_cart"),
    ):
        mock_engine = MagicMock()
        mock_engine.commit_appointment.return_value = MagicMock(id=123)
        mock_engine_func.return_value = mock_engine

        view = BookingCommitView.as_view()
        response = view(request)

        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        if response.status_code != 302 and "HX-Redirect" not in response.headers:
            print("ERROR DETECTED. Content Preview:")
            print(response.content.decode()[:1000])


if __name__ == "__main__":
    debug_wizard()
    debug_commit()

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.cookie import CookieStorage
from django.test import RequestFactory
from django.urls import reverse
from features.booking.dto.public_cart import PublicCart
from features.booking.views.public.commit import BookingCommitView
from tests.factories.booking import AppointmentFactory


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def mock_request(rf):
    request = rf.post(reverse("booking:commit"), data={})
    request.user = AnonymousUser()
    # Mock messages with CookieStorage (avoids session dependency)
    request._messages = CookieStorage(request)
    # Mock session
    request.session = {}
    return request


@pytest.fixture
def mock_cart():
    cart = MagicMock(spec=PublicCart)
    cart.is_empty.return_value = False
    cart.mode = "same_day"
    cart.is_ready_same_day.return_value = True
    cart.contact = {}
    return cart


@pytest.mark.django_db
class TestBookingCommitView:
    def test_post_empty_cart_error(self, mock_request, mock_cart):
        mock_cart.is_empty.return_value = True

        with patch("features.booking.views.public.commit.get_cart", return_value=mock_cart):
            view = BookingCommitView.as_view()
            response = view(mock_request)

        assert response.status_code == 200
        assert "The cart is empty" in response.content.decode("utf-8")
        # Or "Der Warenkorb ist leer" if localized, but log says "The cart is empty"

    def test_post_missing_contact_data_error(self, mock_request, mock_cart):
        mock_request.POST = {"first_name": "", "last_name": "Test", "cancellation_policy": "on", "consent": "on"}

        with (
            patch("features.booking.views.public.commit.get_cart", return_value=mock_cart),
            patch("features.booking.views.public.commit.save_cart"),
        ):
            view = BookingCommitView.as_view()
            response = view(mock_request)

        assert response.status_code == 200
        assert "bk-error-alert" in response.content.decode("utf-8")
        assert "first name" in response.content.decode("utf-8").lower()

    @patch("features.booking.views.public.commit.get_booking_engine_gateway")
    @patch("features.conversations.services.notifications._get_engine")
    @patch("features.booking.views.public.commit.clear_cart")
    def test_post_success_single_appointment(
        self, mock_clear, mock_notify_engine, mock_gateway_fn, mock_request, mock_cart
    ):
        # Setup
        mock_cart.date = "2024-01-01"
        mock_cart.time = "10:00"
        mock_cart.service_ids.return_value = [1]

        appt = AppointmentFactory()
        mock_gateway = MagicMock()
        mock_gateway.create_booking.return_value = appt
        mock_gateway_fn.return_value = mock_gateway

        mock_request.POST = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "12345",
            "cancellation_policy": "on",
            "consent": "on",
        }

        with (
            patch("features.booking.views.public.commit.get_cart", return_value=mock_cart),
            patch("features.booking.views.public.commit.save_cart"),
        ):
            view = BookingCommitView.as_view()
            response = view(mock_request)

        assert response.status_code == 200
        assert response.has_header("HX-Redirect")
        assert response["HX-Redirect"] == reverse("booking:success_single", kwargs={"token": appt.finalize_token})
        mock_clear.assert_called_once()


@pytest.mark.django_db
class TestBookingSuccessViews:
    def test_success_single_view(self):
        from django.test import Client

        client = Client()
        appt = AppointmentFactory()
        url = reverse("booking:success_single", kwargs={"token": appt.finalize_token})

        response = client.get(url)

        assert response.status_code == 200
        assert appt.service.name in response.content.decode("utf-8")

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse
from features.booking.dto.public_cart import PublicCart
from features.booking.views.public.wizard import BookingWizardView


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def mock_cart():
    from features.booking.dto.public_cart import PublicCartItem

    # Use real PublicCart instead of MagicMock for better template compatibility
    cart = PublicCart(items=[PublicCartItem(service_id=1, service_title="Test", duration=60, price=Decimal("100.00"))])
    return cart


@pytest.mark.django_db
class TestBookingWizardView:
    def test_get_wizard_basic_render(self, rf, mock_cart):
        request = rf.get(reverse("booking:booking_wizard"))
        request.user = AnonymousUser()

        mock_provider = MagicMock()
        mock_provider.get_public_services.return_value = [
            {
                "id": 1,
                "slug": "test-service",
                "title": "Test",
                "duration": 60,
                "price": "100.00",
                "category_slug": "cat",
                "category_name": "Category",
            }
        ]

        with (
            patch("features.booking.views.public.wizard.get_cart", return_value=mock_cart),
            patch("features.booking.views.public.wizard.get_booking_project_data_provider", return_value=mock_provider),
        ):
            view = BookingWizardView.as_view()
            response = view(request)

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Check for the main wizard content area and ensure empty state is NOT shown
        assert "booking-wizard-content" in content
        assert "bk-empty-state" not in content

    def test_get_wizard_prefill_service(self, rf, mock_cart):
        request = rf.get(reverse("booking:booking_wizard"), data={"service": "new-service"})
        request.user = AnonymousUser()

        mock_provider = MagicMock()
        mock_provider.get_public_services.return_value = [
            {
                "id": 2,
                "slug": "new-service",
                "title": "New",
                "duration": 30,
                "price": "50.00",
                "category_slug": "cat",
                "category_name": "Category",
            }
        ]

        with (
            patch("features.booking.views.public.wizard.get_cart", return_value=mock_cart),
            patch("features.booking.views.public.wizard.get_booking_project_data_provider", return_value=mock_provider),
            patch("features.booking.views.public.wizard.save_cart") as mock_save,
        ):
            view = BookingWizardView.as_view()
            response = view(request)

        assert response.status_code == 200
        # Check that add was called (PublicCart was modified: 1 initial + 1 new)
        assert len(mock_cart.items) == 2
        mock_save.assert_called_once_with(request, mock_cart)

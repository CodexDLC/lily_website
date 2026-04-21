from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory

from src.lily_backend.cabinet.views.booking import (
    BookingSettingsView,
)
from src.lily_backend.cabinet.views.services import (
    CategoryStatusToggleView,
    ServiceQuickEditView,
    ServicesListView,
)


@pytest.mark.unit
class TestCabinetServicesViewsExtra:
    def setup_method(self):
        self.factory = RequestFactory()

    @patch("src.lily_backend.cabinet.views.services.ServiceCategory")
    def test_services_list_with_category(self, mock_category_class):
        """Test ServicesListView with category_slug (lines 41, 49)."""
        view = ServicesListView()
        view.kwargs = {"category_slug": "haircut"}
        request = self.factory.get("/services/haircut/")
        request.user = MagicMock()
        request.user.is_staff = True
        view.request = request

        mock_service_model = MagicMock()
        view.model = mock_service_model

        # Simple chain mocking
        mock_qs = MagicMock()
        mock_service_model._default_manager.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs

        # Mocking category
        mock_category = MagicMock()
        mock_category_class.objects.filter.return_value.first.return_value = mock_category

        # Execute get_queryset
        qs = view.get_queryset()
        assert qs == mock_qs
        # Verify it was called with category__slug
        mock_qs.filter.assert_any_call(category__slug="haircut")

        # Execute get_context_data
        with patch("src.lily_backend.cabinet.views.services.ListView.get_context_data", return_value={}):
            ctx = view.get_context_data()
            assert ctx["active_category"] == mock_category

    def test_service_quick_edit_invalid(self):
        """Test ServiceQuickEditView form_invalid (line 70)."""
        view = ServiceQuickEditView()
        view.object = MagicMock()
        form = MagicMock()
        form.errors = {"price": ["Invalid"]}

        response = view.form_invalid(form)
        assert response.status_code == 400
        import json

        data = json.loads(response.content)
        assert data["status"] == "error"

    @patch("src.lily_backend.cabinet.views.services.get_object_or_404")
    def test_category_status_toggle(self, mock_get_obj):
        """Test CategoryStatusToggleView (lines 76-89)."""
        view = CategoryStatusToggleView()
        mock_category = MagicMock()
        mock_category.is_active = True
        mock_get_obj.return_value = mock_category

        request = self.factory.post("/toggle/1/", {"field": "is_active"})
        request.user = MagicMock()

        with patch("src.lily_backend.cabinet.views.services.render") as mock_render:
            view.post(request, pk=1)
            assert mock_category.is_active is False
            mock_category.save.assert_called_once()
            mock_render.assert_called_once()


@pytest.mark.unit
class TestBookingSettingsExtra:
    def setup_method(self):
        self.factory = RequestFactory()

    @patch("src.lily_backend.cabinet.views.booking.BookingSettings")
    @patch("src.lily_backend.cabinet.views.booking.BookingSettingsForm")
    def test_booking_settings_post_invalid(self, mock_form_class, mock_settings_class):
        """Test BookingSettingsView POST with invalid form (line 233)."""
        view = BookingSettingsView()
        view.request = self.factory.get("/settings/")

        mock_instance = MagicMock()
        mock_settings_class.load.return_value = mock_instance

        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_form_class.return_value = mock_form

        request = self.factory.post("/settings/", {"some": "data"})
        request.user = MagicMock()

        with patch.object(view, "render_to_response") as mock_render:
            view.post(request)
            mock_render.assert_called_once()
            args, kwargs = mock_render.call_args
            assert args[0]["form"] == mock_form

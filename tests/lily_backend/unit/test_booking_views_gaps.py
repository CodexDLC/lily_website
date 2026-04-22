from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory
from features.booking.booking_settings import BookingSettings

from src.lily_backend.cabinet.views.booking import (
    BookingDayFetchView,
    BookingGroupActionView,
    BookingGroupListView,
    BookingSettingsForm,
    BookingSlotFetchView,
)


@pytest.mark.unit
class TestBookingViewsGaps:
    def setup_method(self):
        self.factory = RequestFactory()

    def test_booking_settings_form_day_rows(self):
        """Test the day_rows property of BookingSettingsForm."""
        instance = MagicMock(spec=BookingSettings)
        # Mocking access to form fields
        form = BookingSettingsForm(instance=instance)
        with patch.object(BookingSettingsForm, "__getitem__", return_value="mock_field"):
            rows = form.day_rows
            assert len(rows) == 7
            assert rows[0]["key"] == "monday"
            assert rows[0]["label"] == "Monday"

    @patch("features.booking.models.AppointmentGroup")
    def test_booking_group_list_htmx(self, mock_group_class):
        """Test BookingGroupListView with HTMX request."""
        mock_qs = MagicMock()
        mock_group_class.objects.select_related.return_value.prefetch_related.return_value.order_by.return_value = (
            mock_qs
        )
        mock_qs.__getitem__.return_value = []

        view = BookingGroupListView()
        request = self.factory.get("/groups/", HTTP_HX_REQUEST="true")
        request.user = MagicMock()
        view.request = request

        with patch.object(view, "get_context_data", return_value={}):
            response = view.get(request)
            assert response.status_code == 200

    @patch("features.booking.models.AppointmentGroup")
    def test_booking_group_list_standard_with_filter(self, mock_group_class):
        """Test BookingGroupListView with standard request and status filter."""
        mock_qs = MagicMock()
        mock_group_class.objects.select_related.return_value.prefetch_related.return_value.order_by.return_value = (
            mock_qs
        )
        mock_qs.filter.return_value = mock_qs
        mock_qs.__getitem__.return_value = []

        view = BookingGroupListView()
        request = self.factory.get("/groups/", {"status": "confirmed"})
        request.user = MagicMock()
        view.request = request

        with patch.object(view, "get_context_data", return_value={}):
            response = view.get(request)
            assert response.status_code == 200
            mock_qs.filter.assert_called_with(status="confirmed")

    @patch("src.lily_backend.cabinet.views.booking.get_object_or_404")
    def test_booking_group_action_htmx(self, mock_get_object):
        """Test BookingGroupActionView POST actions with HTMX."""
        mock_group = MagicMock()
        mock_get_object.return_value = mock_group

        view = BookingGroupActionView()

        # Action: confirm_all
        request = self.factory.post("/groups/1/confirm_all/", HTTP_HX_REQUEST="true")
        response = view.post(request, pk=1, action="confirm_all")
        mock_group.confirm_all.assert_called_once()
        assert response["HX-Redirect"] == "/cabinet/booking/groups/"

        # Action: cancel_all
        request = self.factory.post("/groups/1/cancel_all/", {"reason": "test"}, HTTP_HX_REQUEST="true")
        response = view.post(request, pk=1, action="cancel_all")
        mock_group.cancel_all.assert_called_with(reason="test", note="")

    def test_booking_slot_fetch_error_branch(self):
        """Test BookingSlotFetchView when parameters are missing."""
        view = BookingSlotFetchView()
        request = self.factory.get("/slots/", {"date": ""})  # Missing service_ids
        response = view.get(request)
        assert response.status_code == 200
        import json

        data = json.loads(response.content)
        assert data["slots"] == []

    @patch("src.lily_backend.cabinet.views.booking.CabinetBookingAvailabilityService")
    def test_booking_slot_fetch_success(self, mock_service_class):
        """Test BookingSlotFetchView success branch."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_slots.return_value = ["slot1"]

        view = BookingSlotFetchView()
        request = self.factory.get("/slots/", {"date": "2026-01-01", "service_ids": "1,2", "master_id": "10"})
        response = view.get(request)

        assert response.status_code == 200
        import json

        data = json.loads(response.content)
        assert data["slots"] == ["slot1"]

    def test_booking_day_fetch_error_branch(self):
        """Test BookingDayFetchView when service_ids are missing."""
        view = BookingDayFetchView()
        request = self.factory.get("/days/", {"service_ids": ""})
        response = view.get(request)
        assert response.status_code == 200
        import json

        data = json.loads(response.content)
        assert data["available_dates"] == []

    @patch("src.lily_backend.cabinet.views.booking.CabinetBookingAvailabilityService")
    @patch("src.lily_backend.cabinet.views.booking.BookingSettings")
    @patch("django.utils.timezone.localdate")
    def test_booking_day_fetch_success(self, mock_localdate, mock_settings_class, mock_service_class):
        """Test BookingDayFetchView success branch."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_available_dates.return_value = ["2026-01-01"]

        mock_settings = MagicMock()
        mock_settings.max_advance_days = 30
        mock_settings_class.load.return_value = mock_settings

        mock_localdate.return_value = "2026-01-01"

        view = BookingDayFetchView()
        request = self.factory.get("/days/", {"service_ids": "1,2"})
        response = view.get(request)

        assert response.status_code == 200
        import json

        data = json.loads(response.content)
        assert data["available_dates"] == ["2026-01-01"]

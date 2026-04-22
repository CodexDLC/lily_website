from datetime import time
from unittest.mock import MagicMock, patch

import pytest
from features.booking.services.cabinet import BookingCabinetWorkflowService


class TestBookingCabinetWorkflow:
    @pytest.fixture
    def mock_provider(self):
        return MagicMock()

    @pytest.fixture
    def mock_settings(self):
        settings = MagicMock()
        settings.max_advance_days = 30
        settings.step_minutes = 30
        # Mock get_day_schedule to return (9:00, 18:00) for all days
        settings.get_day_schedule.return_value = (time(9, 0), time(18, 0))
        return settings

    @pytest.fixture
    def service(self, mock_provider, mock_settings):
        with (
            patch("features.booking.booking_settings.BookingSettings.load", return_value=mock_settings),
            patch("features.booking.services.cabinet.CabinetBookingAvailabilityService", autospec=True),
        ):
            return BookingCabinetWorkflowService(provider=mock_provider)

    def test_client_styling_is_deterministic(self, service):
        name = "Anna Schmidt"
        color1 = service._get_client_color(name)
        color2 = service._get_client_color(name)
        border1 = service._get_client_border(name)

        assert color1 == color2
        assert color1.startswith("hsla(")
        assert border1.startswith("hsl(")

        # Different names should have different colors (probabilistically)
        color_other = service._get_client_color("Other Name")
        assert color1 != color_other

    def test_get_schedule_context_grid_calc(self, service, mock_provider, mock_settings):
        # Mock provider data
        mock_provider.get_cabinet_masters.return_value = [
            {"id": 1, "name": "Master Lily"},
            {"id": 2, "name": "Master Rose"},
        ]
        mock_provider.get_cabinet_appointments.return_value = [
            {
                "id": 101,
                "master_id": 1,
                "date": "2026-04-17",
                "time": "10:00",
                "duration": 60,
                "client_name": "Test Client",
                "status": "pending",
                "service_title": "Haircut",
                "price": 50,
            }
        ]

        request = MagicMock()
        request.GET.get.side_effect = lambda k, default=None: "2026-04-17" if k == "date" else default

        with patch("features.booking.services.cabinet.reverse", return_value="/mock/url/"):
            context = service.get_schedule_context(request)

        calendar = context["calendar"]
        assert len(calendar.cols) == 2
        assert calendar.cols[0]["name"] == "Master Lily"

        # Check event transformation
        assert len(calendar.events) == 1
        event = calendar.events[0]
        assert event.title == "Test Client"
        assert event.col == 0  # Master Lily
        # 10:00 is (10-9)*2 = 2nd row (index 2) if 9:00 is row 0
        assert event.row == 2
        assert event.span == 2  # 60 min / 30 min step

    def test_modal_url_construction(self, service):
        with patch("features.booking.services.cabinet.reverse", return_value="/booking/10/"):
            url = service.modal_url(10, mode="edit")
            assert url == "/booking/10/?mode=edit"

            url_no_mode = service.modal_url(10)
            assert url_no_mode == "/booking/10/"

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from features.booking.services.cabinet_availability import CabinetBookingAvailabilityService


class TestCabinetBookingAvailability:
    @pytest.fixture
    def mock_gateway(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_gateway):
        return CabinetBookingAvailabilityService(gateway=mock_gateway)

    def test_get_available_dates_logic(self, service):
        # Mock MasterWorkingDay.objects.filter(...).values_list(...).distinct()
        mock_qs = MagicMock()
        mock_qs.values_list.return_value.distinct.return_value = [0, 2, 4]  # Mon, Wed, Fri

        with patch("features.booking.models.MasterWorkingDay.objects.filter", return_value=mock_qs):
            start_date = date(2026, 4, 13)  # Monday
            horizon = 7

            available = service.get_available_dates(start_date=start_date, horizon=horizon, service_ids=[1])

            # Should have 2026-04-13 (Mon), 2026-04-15 (Wed), 2026-04-17 (Fri)
            assert "2026-04-13" in available
            assert "2026-04-15" in available
            assert "2026-04-17" in available
            assert "2026-04-14" not in available
            assert len(available) == 3

    def test_get_available_dates_no_services(self, service):
        available = service.get_available_dates(start_date=date(2026, 4, 13), horizon=7, service_ids=[])
        assert available == set()

    def test_build_picker_days_integration(self, service):
        # We mock the internal get_available_dates and the library build_picker_day_rows
        available_dates = {"2026-04-13", "2026-04-15"}
        mock_rows = [{"date": "2026-04-13", "is_available": True}]

        with (
            patch.object(service, "get_available_dates", return_value=available_dates),
            patch("features.booking.services.cabinet_availability.build_picker_day_rows", return_value=mock_rows),
        ):
            rows = service.build_picker_days(start_date=date(2026, 4, 13), horizon=7, service_ids=[1])

            assert rows == mock_rows

    def test_get_slots_success(self, service, mock_gateway):
        mock_gateway.get_available_slots.return_value = ["slot1", "slot2"]

        with patch("features.booking.services.cabinet_availability.normalize_slot_payload", side_effect=lambda x: x):
            slots = service.get_slots(booking_date="2026-04-13", service_ids=[1])

            assert slots == ["slot1", "slot2"]
            mock_gateway.get_available_slots.assert_called_once()

    def test_get_slots_invalid_date(self, service):
        slots = service.get_slots(booking_date="invalid-date", service_ids=[1])
        assert slots == []

    def test_get_slots_gateway_error(self, service, mock_gateway):
        mock_gateway.get_available_slots.side_effect = Exception("Gateway error")

        slots = service.get_slots(booking_date="2026-04-13", service_ids=[1])
        assert slots == []

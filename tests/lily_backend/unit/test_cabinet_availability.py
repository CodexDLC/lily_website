from datetime import date
from unittest.mock import MagicMock

import pytest
from features.booking.services.cabinet_availability import CabinetBookingAvailabilityService
from tests.factories.booking import MasterFactory, MasterWorkingDayFactory
from tests.factories.main import ServiceFactory


@pytest.mark.django_db
class TestCabinetAvailabilityService:
    def test_get_available_dates(self):
        master = MasterFactory(working_days=False)
        booking_service = ServiceFactory()
        booking_service.masters.add(master)
        MasterWorkingDayFactory(master=master, weekday=0)  # Monday

        service = CabinetBookingAvailabilityService()
        dates = service.get_available_dates(
            start_date=date(2024, 1, 1),  # Monday
            horizon=7,
            service_ids=[booking_service.pk],
        )

        assert "2024-01-01" in dates

    def test_get_slots(self):
        mock_gateway = MagicMock()
        mock_gateway.get_available_slots.return_value = ["09:00", "10:00"]

        service = CabinetBookingAvailabilityService(gateway=mock_gateway)
        slots = service.get_slots(booking_date="2024-01-01", service_ids=[1])

        assert slots == ["09:00", "10:00"]
        mock_gateway.get_available_slots.assert_called_once()

    def test_get_slots_returns_empty_when_gateway_fails(self):
        mock_gateway = MagicMock()
        mock_gateway.get_available_slots.side_effect = RuntimeError("gateway down")

        service = CabinetBookingAvailabilityService(gateway=mock_gateway)
        slots = service.get_slots(booking_date="2024-01-01", service_ids=[1])

        assert slots == []

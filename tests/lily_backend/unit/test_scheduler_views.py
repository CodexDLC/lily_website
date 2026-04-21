from decimal import Decimal
from unittest.mock import patch

import pytest
from features.booking.dto.public_cart import PublicCart, PublicCartItem
from features.booking.views.public.scheduler import SchedulerCalendarView, SchedulerConfirmTimeView, SchedulerSlotsView


def _cart():
    return PublicCart(
        items=[
            PublicCartItem(
                service_id=1,
                service_title="Service",
                duration=60,
                price=Decimal("50.00"),
            )
        ]
    )


@pytest.mark.django_db
class TestSchedulerViews:
    @patch("features.booking.views.public.scheduler.CabinetBookingAvailabilityService")
    @patch("features.booking.views.public.scheduler.get_cart")
    @patch("features.booking.views.public.scheduler.render")
    def test_scheduler_calendar_view(self, mock_render, mock_get, mock_service, rf):
        request = rf.get("/booking/scheduler/calendar/")
        request.session = {}
        mock_get.return_value = _cart()
        mock_service.return_value.get_available_dates.return_value = {"2024-01-01"}

        view = SchedulerCalendarView()
        view.request = request
        view.get(request)

        mock_render.assert_called()
        assert mock_render.call_args.args[1] == "features/booking/partials/calendar.html"
        mock_service.return_value.get_available_dates.assert_called()

    @patch("features.booking.views.public.scheduler.CabinetBookingAvailabilityService")
    @patch("features.booking.views.public.scheduler.get_cart")
    @patch("features.booking.views.public.scheduler.render")
    def test_scheduler_slots_view(self, mock_render, mock_get, mock_service, rf):
        request = rf.get("/booking/scheduler/slots/", {"date": "2024-01-01"})
        request.session = {}
        mock_get.return_value = _cart()
        mock_service.return_value.get_slots.return_value = ["09:00"]

        view = SchedulerSlotsView()
        view.request = request
        view.get(request)

        mock_service.return_value.get_slots.assert_called_once_with(
            booking_date="2024-01-01",
            service_ids=[1],
        )
        mock_render.assert_called()

    @patch("features.booking.views.public.scheduler.get_cart")
    @patch("features.booking.views.public.scheduler.save_cart")
    @patch("features.booking.views.public.scheduler.render")
    def test_scheduler_confirm_time_view(self, mock_render, mock_save, mock_get, rf):
        request = rf.post("/booking/scheduler/confirm/", {"time": "10:00", "date": "2024-01-01"})
        request.session = {}
        cart = _cart()
        mock_get.return_value = cart

        view = SchedulerConfirmTimeView()
        view.request = request
        view.post(request)

        assert cart.date == "2024-01-01"
        assert cart.time == "10:00"
        mock_save.assert_called_with(request, cart)
        mock_render.assert_called()

import pytest
from features.booking.services.notifications import (
    handle_booking_cancelled,
    handle_booking_confirmed,
    handle_booking_group_received,
    handle_booking_no_show,
    handle_booking_received,
    handle_booking_rescheduled,
)
from tests.factories.booking import (
    AppointmentFactory,
    AppointmentGroupFactory,
    AppointmentGroupItemFactory,
)


@pytest.mark.django_db
class TestBookingNotifications:
    def test_handle_booking_confirmed(self):
        appt = AppointmentFactory()
        spec = handle_booking_confirmed(appt)
        assert spec.template_name == "emails/booking_confirmed.html"
        assert spec.event_type == "booking.confirmed"
        assert spec.context["id"] == appt.pk
        assert spec.context["service_name"] == appt.service.name
        assert spec.context["master_name"] == appt.master.name
        assert "datetime" in spec.context

    def test_handle_booking_cancelled(self):
        appt = AppointmentFactory()
        spec = handle_booking_cancelled(appt)
        assert spec.template_name == "emails/booking_cancelled.html"
        assert spec.event_type == "booking.cancelled"
        assert spec.context["id"] == appt.pk
        assert "reason_text" in spec.context

    def test_handle_booking_received(self):
        appt = AppointmentFactory()
        spec = handle_booking_received(appt)
        assert spec.template_name == "bk_receipt"
        assert spec.event_type == "booking.received"
        assert spec.context["service_name"] == appt.service.name

    def test_handle_booking_group_received(self):
        group = AppointmentGroupFactory()
        appt1 = AppointmentFactory()
        appt2 = AppointmentFactory()
        AppointmentGroupItemFactory(group=group, appointment=appt1, order=0)
        AppointmentGroupItemFactory(group=group, appointment=appt2, order=1)

        spec = handle_booking_group_received(group)
        assert spec.template_name == "bk_group_booking"
        assert spec.event_type == "booking.received"
        assert len(spec.context["items"]) == 2
        assert spec.context["items"][0]["service_name"] == appt1.service.name
        assert spec.context["items"][1]["service_name"] == appt2.service.name

    def test_handle_booking_rescheduled(self):
        appt = AppointmentFactory()
        spec = handle_booking_rescheduled(appt)
        assert spec.template_name == "bk_reschedule"
        assert spec.event_type == "booking.rescheduled"

    def test_handle_booking_no_show(self):
        appt = AppointmentFactory()
        spec = handle_booking_no_show(appt)
        assert spec.template_name == "bk_no_show"
        assert spec.event_type == "booking.no_show"

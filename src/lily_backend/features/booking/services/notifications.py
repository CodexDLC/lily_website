from __future__ import annotations

from typing import TYPE_CHECKING, Any

from codex_django.notifications import NotificationDispatchSpec, notification_handler

if TYPE_CHECKING:
    from features.booking.models import Appointment


def build_booking_notification_context(appt: Appointment) -> dict[str, Any]:
    """Extract standard context for booking notifications."""
    return {
        "service": appt.service.name,
        "master": appt.master.name,
        "datetime": appt.datetime_start.strftime("%d.%m.%Y %H:%M"),
    }


@notification_handler("booking.confirmed")
def handle_booking_confirmed(appt: Appointment) -> NotificationDispatchSpec:
    """Handler for confirmed appointments."""
    return NotificationDispatchSpec(
        recipient_email=appt.client.email,
        client_name=appt.client.first_name,
        subject_key="bk_confirmation_subject",
        event_type="booking.confirmed",
        template_name="emails/booking_confirmed.html",
        channels=["email"],
        language=appt.lang,
        context=build_booking_notification_context(appt),
    )


@notification_handler("booking.cancelled")
def handle_booking_cancelled(appt: Appointment) -> NotificationDispatchSpec:
    """Handler for cancelled appointments."""
    context = build_booking_notification_context(appt)
    context["reason_text"] = appt.get_cancel_reason_display()

    return NotificationDispatchSpec(
        recipient_email=appt.client.email,
        client_name=appt.client.first_name,
        subject_key="bk_cancellation_subject",
        event_type="booking.cancelled",
        template_name="emails/booking_cancelled.html",
        channels=["email"],
        language=appt.lang,
        context=context,
    )


@notification_handler("booking.received")
def handle_booking_received(appt: Appointment) -> NotificationDispatchSpec:
    """Handler for new booking requests (receipt)."""
    return NotificationDispatchSpec(
        recipient_email=appt.client.email,
        client_name=appt.client.first_name,
        subject_key="bk_receipt_subject",
        event_type="booking.received",
        template_name="bk_receipt",  # No dedicated HTML found, using block
        channels=["email"],
        language=appt.lang,
        context=build_booking_notification_context(appt),
    )


@notification_handler("booking.no_show")
def handle_booking_no_show(appt: Appointment) -> NotificationDispatchSpec:
    """Handler for no-show appointments."""
    return NotificationDispatchSpec(
        recipient_email=appt.client.email,
        client_name=appt.client.first_name,
        subject_key="bk_noshow_subject",
        event_type="booking.no_show",
        template_name="bk_no_show",
        channels=["email"],
        language=appt.lang,
        context=build_booking_notification_context(appt),
    )


@notification_handler("booking.rescheduled")
def handle_booking_rescheduled(appt: Appointment) -> NotificationDispatchSpec:
    """Handler for reschedule proposals."""
    return NotificationDispatchSpec(
        recipient_email=appt.client.email,
        client_name=appt.client.first_name,
        subject_key="bk_reschedule_subject",
        event_type="booking.rescheduled",
        template_name="bk_reschedule",
        channels=["email"],
        language=appt.lang,
        context=build_booking_notification_context(appt),
    )

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from codex_django.notifications import NotificationDispatchSpec, notification_handler

from features.notifications.services.recipients import get_admin_notification_emails

from .admin_context import build_admin_booking_context

if TYPE_CHECKING:
    from features.booking.models import Appointment, AppointmentGroup


def build_booking_notification_context(appt: Appointment) -> dict[str, Any]:
    """Extract standard context for booking notifications."""
    service_name = appt.service.name
    master_name = appt.master.name
    formatted_datetime = appt.datetime_start.strftime("%d.%m.%Y %H:%M")
    return {
        "id": appt.pk,
        "service": service_name,
        "service_name": service_name,
        "master": master_name,
        "master_name": master_name,
        "datetime": formatted_datetime,
        "duration_minutes": appt.duration_minutes,
        "price": str(appt.price),
    }


def build_booking_group_notification_context(group: AppointmentGroup) -> dict[str, Any]:
    """Extract one email context for a same-day chain booking."""
    items = []
    total_price = Decimal("0")
    total_duration = 0
    booking_date = ""
    booking_datetime = ""
    language = "de"

    for group_item in group.items.select_related("appointment__service", "appointment__master").order_by("order"):
        appt = group_item.appointment
        language = appt.lang or language
        total_price += appt.price or 0
        total_duration += appt.duration_minutes or 0
        if not booking_date:
            booking_date = appt.datetime_start.strftime("%d.%m.%Y")
            booking_datetime = appt.datetime_start.strftime("%d.%m.%Y %H:%M")
        items.append(
            {
                "service_name": appt.service.name,
                "name": appt.service.name,
                "master_name": appt.master.name,
                "time": appt.datetime_start.strftime("%H:%M"),
                "price": str(appt.price),
                "duration_minutes": appt.duration_minutes,
            }
        )

    client = group.client
    first_name = getattr(client, "first_name", "") if client else ""
    last_name = getattr(client, "last_name", "") if client else ""

    return {
        "group_id": group.pk,
        "items": items,
        "date": booking_date,
        "booking_date": booking_date,
        "datetime": booking_datetime,
        "total_price": str(total_price),
        "total_duration": total_duration,
        "first_name": first_name,
        "last_name": last_name,
        "client_phone": getattr(client, "phone", "") if client else "",
        "client_email": getattr(client, "email", "") if client else "",
        "booking_language": language,
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


@notification_handler("booking.group_received")
def handle_booking_group_received(group: AppointmentGroup) -> NotificationDispatchSpec:
    """Handler for same-day chain booking requests (one receipt for the group)."""
    context = build_booking_group_notification_context(group)
    client = group.client
    return NotificationDispatchSpec(
        recipient_email=getattr(client, "email", "") if client else "",
        client_name=getattr(client, "first_name", "") if client else "",
        subject_key="bk_receipt_subject",
        event_type="booking.received",
        template_name="bk_group_booking",
        channels=["email"],
        language=context["booking_language"],
        context=context,
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


def _iter_admin_booking_specs(appt_or_group, event_type: str, template_name: str, subject_key: str):
    is_group = hasattr(appt_or_group, "items")
    client = appt_or_group.client

    if is_group:
        context_base = build_booking_group_notification_context(appt_or_group)
        language = context_base.get("booking_language", "de")
    else:
        language = appt_or_group.lang or "de"

    for email in get_admin_notification_emails():
        context = build_admin_booking_context(appt_or_group, email)
        yield NotificationDispatchSpec(
            recipient_email=email,
            client_name=client.first_name if client else "",
            subject_key=subject_key,
            event_type=event_type,
            template_name=template_name,
            channels=["email"],
            language=language,
            context=context,
        )


@notification_handler("booking.received")
def handle_booking_received_admin(appt):
    return list(
        _iter_admin_booking_specs(appt, "booking.received", "emails/admin_booking_received.html", "bk_receipt_subject")
    )


@notification_handler("booking.group_received")
def handle_booking_group_received_admin(group):
    return list(
        _iter_admin_booking_specs(
            group, "booking.received", "emails/admin_booking_group_received.html", "bk_receipt_subject"
        )
    )


@notification_handler("booking.cancelled")
def handle_booking_cancelled_admin(appt):
    if getattr(appt, "_booking_origin", "client") == "staff":
        return []
    return list(
        _iter_admin_booking_specs(
            appt, "booking.cancelled", "emails/admin_booking_cancelled.html", "bk_cancellation_subject"
        )
    )


@notification_handler("booking.rescheduled")
def handle_booking_rescheduled_admin(appt):
    if getattr(appt, "_booking_origin", "client") == "staff":
        return []
    return list(
        _iter_admin_booking_specs(
            appt, "booking.rescheduled", "emails/admin_booking_rescheduled.html", "bk_reschedule_subject"
        )
    )

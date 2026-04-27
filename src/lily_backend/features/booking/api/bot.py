from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from features.booking.models import Appointment
from ninja import Router, Schema
from system.api.auth import require_internal_scope

router = Router(tags=["Booking Worker"])

REMINDER_WINDOW_HOURS = 3


class ReschedulePayload(Schema):
    proposed_datetime_str: str  # Format: DD.MM.YYYY HH:MM


@router.post("/appointments/{appointment_id}/propose-reschedule")
def propose_reschedule(request, appointment_id: int, payload: ReschedulePayload):
    require_internal_scope(request, "booking.worker")
    appt = get_object_or_404(Appointment, id=appointment_id)

    try:
        new_dt = datetime.strptime(payload.proposed_datetime_str, "%d.%m.%Y %H:%M")
        new_dt_aware = timezone.make_aware(new_dt)
        appt.datetime_start = new_dt_aware
        appt.save(update_fields=["datetime_start", "updated_at"])
        appt.propose_reschedule()
        return {"success": True, "message": "Rescheduling proposed."}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/appointments/{appointment_id}/no-show")
def mark_no_show(request, appointment_id: int):
    require_internal_scope(request, "booking.worker")
    appt = get_object_or_404(Appointment, id=appointment_id)
    appt.mark_no_show()
    return {"success": True}


@router.get("/appointments/upcoming")
def get_upcoming(request):
    require_internal_scope(request, "booking.worker")
    appts = Appointment.objects.filter(
        datetime_start__gte=timezone.now(), status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED]
    ).select_related("client", "service")[:10]

    return [
        {
            "id": a.id,
            "client": a.client.first_name if a.client else "Unknown",
            "service": a.service.title,
            "datetime": a.datetime_start.isoformat(),
            "status": a.status,
        }
        for a in appts
    ]


@router.get("/appointments/reminders-due")
def get_reminders_due(request):
    require_internal_scope(request, "booking.worker")
    now = timezone.now()
    window_end = now + timedelta(hours=REMINDER_WINDOW_HOURS)
    appts = Appointment.objects.filter(
        status=Appointment.STATUS_CONFIRMED,
        datetime_start__gte=now,
        datetime_start__lte=window_end,
        reminder_sent=False,
        client__email__gt="",
    ).select_related("client", "service", "master")

    result = []
    for a in appts:
        local_start = timezone.localtime(a.datetime_start)
        result.append(
            {
                "id": a.id,
                "client_email": a.client.email if a.client else "",
                "name": a.client.first_name if a.client else "",
                "service_name": a.service.name,
                "datetime": local_start.strftime("%d.%m.%Y %H:%M"),
                "lang": a.lang or "de",
                "master_name": a.master.name,
            }
        )
    return result


@router.post("/appointments/{appointment_id}/mark-reminder-sent")
def mark_reminder_sent(request, appointment_id: int):
    require_internal_scope(request, "booking.worker")
    appt = get_object_or_404(Appointment, id=appointment_id)
    appt.reminder_sent = True
    appt.reminder_sent_at = timezone.now()
    appt.save(update_fields=["reminder_sent", "reminder_sent_at", "updated_at"])
    return {"success": True}

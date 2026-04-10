from datetime import datetime

from django.shortcuts import get_object_or_404
from django.utils import timezone
from features.booking.models import Appointment
from ninja import Router, Schema

router = Router(tags=["Telegram Bot"])


class ReschedulePayload(Schema):
    proposed_datetime_str: str  # Format: DD.MM.YYYY HH:MM


@router.post("/appointments/{appointment_id}/propose-reschedule")
def propose_reschedule(request, appointment_id: int, payload: ReschedulePayload):
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
    appt = get_object_or_404(Appointment, id=appointment_id)
    appt.mark_no_show()
    return {"success": True}


@router.get("/appointments/upcoming")
def get_upcoming(request):
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

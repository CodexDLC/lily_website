from core.logger import log
from django.db.models import QuerySet
from features.booking.models import Appointment


def get_cabinet_appointments(user, client_filter=None, status_filter=None) -> QuerySet[Appointment]:
    """
    Returns a queryset of appointments for the cabinet according to filtering rules.
    If client_filter is provided (usually for personal scope), filters by client.
    """
    log.debug(
        f"Selector: AppointmentSelector | Action: GetCabinetAppointments | user={user.id} | client_filter={client_filter.id if client_filter else 'None'} | status={status_filter}"
    )

    qs = Appointment.objects.select_related("client", "master", "service").order_by("-datetime_start")

    if client_filter:
        qs = qs.filter(client=client_filter)

    if status_filter:
        qs = qs.filter(status=status_filter)

    log.debug(f"Selector: AppointmentSelector | Action: Success | count={qs.count()}")
    return qs

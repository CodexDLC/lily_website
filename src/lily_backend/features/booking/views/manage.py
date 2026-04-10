"""Views for managing appointments via Action Tokens."""

from typing import Any

from django.views.generic import DetailView

from features.booking.models.appointment import Appointment


class AppointmentManageView(DetailView):
    """
    View for managing a specific appointment via its finalize_token.
    Allows clients to view, cancel, or initiate rescheduling.
    """

    model = Appointment
    template_name = "booking/manage_appointment.html"
    slug_field = "finalize_token"
    slug_url_kwarg = "token"
    context_object_name = "appointment"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # Note: In legacy, a separate 'reschedule_token' was a separate random token.
        return context

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView

from features.booking.models import Appointment

from .manage import AppointmentManageView as AppointmentManageView
from .public.cart import CartAddView as CartAddView
from .public.cart import CartRemoveView as CartRemoveView
from .public.cart import CartSetModeView as CartSetModeView
from .public.cart import CartSetStageView as CartSetStageView
from .public.commit import BookingCommitView as BookingCommitView
from .public.commit import BookingSuccessGroupView as BookingSuccessGroupView
from .public.commit import BookingSuccessMultiView as BookingSuccessMultiView
from .public.commit import BookingSuccessSingleView as BookingSuccessSingleView
from .public.scheduler import SchedulerCalendarView as SchedulerCalendarView
from .public.scheduler import SchedulerConfirmTimeView as SchedulerConfirmTimeView
from .public.scheduler import SchedulerSlotsItemView as SchedulerSlotsItemView
from .public.scheduler import SchedulerSlotsView as SchedulerSlotsView
from .public.wizard import BookingWizardView as BookingWizardView


class BookingComingSoonView(TemplateView):
    """Public booking wizard — kept as fallback/redirect target."""

    template_name = "features/booking/coming_soon.html"


class ConfirmAppointmentView(TemplateView):
    """Email action: confirm appointment via token."""

    template_name = "features/booking/confirm_appointment.html"

    def get(self, request, *args, **kwargs):
        token = self.kwargs["token"]
        appt = get_object_or_404(Appointment, finalize_token=token)
        context = self.get_context_data(appointment=appt)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        token = self.kwargs["token"]
        appt = get_object_or_404(Appointment, finalize_token=token)
        try:
            appt.confirm()
            return self.render_to_response(self.get_context_data(appointment=appt, success=True))
        except ValidationError as e:
            return self.render_to_response(self.get_context_data(appointment=appt, error=str(e)))


class CancelAppointmentView(TemplateView):
    """Email action: cancel appointment via token."""

    template_name = "features/booking/cancel_appointment.html"

    def get(self, request, *args, **kwargs):
        token = self.kwargs["token"]
        appt = get_object_or_404(Appointment, finalize_token=token)
        context = self.get_context_data(
            appointment=appt,
            can_cancel=appt.can_cancel(),
            cancel_reasons=Appointment.CANCEL_REASON_CHOICES,
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        token = self.kwargs["token"]
        appt = get_object_or_404(Appointment, finalize_token=token)
        reason = request.POST.get("reason", Appointment.CANCEL_REASON_CLIENT)
        note = request.POST.get("note", "")
        try:
            appt.cancel(reason=reason, note=note)
            from features.conversations.services.notifications import _get_engine

            _get_engine().dispatch_event("booking.cancelled", appt)
            return redirect(reverse("booking:cancel_success"))
        except ValidationError as e:
            return self.render_to_response(self.get_context_data(appointment=appt, error=str(e), can_cancel=False))


class CancelSuccessView(TemplateView):
    template_name = "features/booking/cancel_success.html"


class RescheduleAppointmentView(TemplateView):
    """Email action: reschedule appointment via token."""

    template_name = "features/booking/reschedule_appointment.html"

    def get(self, request, *args, **kwargs):
        token = self.kwargs["token"]
        appt = get_object_or_404(Appointment, finalize_token=token)
        return self.render_to_response(self.get_context_data(appointment=appt))

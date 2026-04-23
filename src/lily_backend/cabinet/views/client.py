import contextlib
import datetime as dt_module
from datetime import datetime
from typing import TYPE_CHECKING, Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import formats, timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, View
from features.booking.models.appointment import Appointment

from cabinet.services.client import ClientService

if TYPE_CHECKING:
    from system.models import Client, UserProfile


class ClientHomeView(LoginRequiredMixin, TemplateView):
    template_name = "cabinet/client/corner.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_space = "client"
        request.cabinet_module = "client"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(ClientService.get_corner_context(self.request))
        return context


class ClientAppointmentsView(LoginRequiredMixin, TemplateView):
    template_name = "cabinet/client/appointments.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_space = "client"
        request.cabinet_module = "client"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(ClientService.get_appointments_context(self.request))
        return context


class ClientManageAppointmentView(LoginRequiredMixin, TemplateView):
    template_name = "cabinet/client/manage_appointment.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_space = "client"
        request.cabinet_module = "client"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        appointment = get_object_or_404(Appointment, finalize_token=self.kwargs["token"])
        hours_until = (appointment.datetime_start - timezone.now()).total_seconds() / 3600
        can_cancel = appointment.can_cancel()
        context["appointment"] = appointment
        context["can_cancel"] = can_cancel
        context["hours_until"] = hours_until
        context["show_loyalty_warning"] = can_cancel and hours_until < 24
        return context


class ClientRescheduleModalView(LoginRequiredMixin, TemplateView):
    """HTMX: returns calendar modal content for reschedule."""

    template_name = "cabinet/client/partials/_reschedule_calendar.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_space = "client"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        from features.booking.booking_settings import BookingSettings
        from features.booking.services.cabinet_availability import CabinetBookingAvailabilityService
        from features.booking.views.public.scheduler import _build_calendar_grid

        context = super().get_context_data(**kwargs)
        appointment = get_object_or_404(Appointment, finalize_token=self.kwargs["token"])
        settings = BookingSettings.load()
        availability = CabinetBookingAvailabilityService(audience="public")
        today = timezone.localdate()

        min_date = today + dt_module.timedelta(days=1 if settings.book_only_from_next_day else 0)
        max_date = today + dt_module.timedelta(days=max(settings.max_advance_days - 1, 0))

        try:
            req_year = int(self.request.GET.get("year", today.year))
            req_month = int(self.request.GET.get("month", today.month))
            req_date = dt_module.date(req_year, req_month, 1)
        except ValueError:
            req_date = today.replace(day=1)

        available_dates = availability.get_available_dates(
            start_date=today,
            horizon=settings.max_advance_days,
            service_ids=[appointment.service_id],
        )
        calendar_data = _build_calendar_grid(
            year=req_date.year,
            month=req_date.month,
            today=today,
            selected_date=None,
            min_date=min_date,
            max_date=max_date,
            available_dates=available_dates,
        )

        prev_date = (req_date - dt_module.timedelta(days=1)).replace(day=1)
        next_date = (req_date.replace(day=28) + dt_module.timedelta(days=4)).replace(day=1)

        context.update(
            {
                "appointment": appointment,
                "calendar_data": calendar_data,
                "month_label": formats.date_format(req_date, "F Y"),
                "year": req_date.year,
                "month": req_date.month,
                "prev_year": prev_date.year,
                "prev_month": prev_date.month,
                "next_year": next_date.year,
                "next_month": next_date.month,
                "can_go_prev": req_date > min_date.replace(day=1),
                "can_go_next": req_date < max_date.replace(day=1),
            }
        )
        return context


class ClientRescheduleSlotsView(LoginRequiredMixin, View):
    """HTMX: time slots for selected date in reschedule modal."""

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        from features.booking.services.cabinet_availability import CabinetBookingAvailabilityService

        appointment = get_object_or_404(Appointment, finalize_token=self.kwargs["token"])
        date_str = request.GET.get("date", "")
        try:
            target_date = dt_module.date.fromisoformat(date_str)
        except ValueError:
            return HttpResponse(status=400)

        availability = CabinetBookingAvailabilityService(audience="public")
        slots = availability.get_slots(
            booking_date=target_date.isoformat(),
            service_ids=[appointment.service_id],
        )
        return render(
            request,
            "cabinet/client/partials/_reschedule_slots.html",
            {
                "slots": slots,
                "date": target_date,
                "appointment": appointment,
            },
        )


class ClientRescheduleConfirmView(LoginRequiredMixin, View):
    """POST: update appointment datetime_start directly, dispatch notification."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        appointment = get_object_or_404(Appointment, finalize_token=self.kwargs["token"])

        # 1. Status and Timing validation
        if not appointment.can_cancel():
            messages.error(request, _("This appointment is too close to its start time or already finished."))
            return redirect(reverse("cabinet:client_manage_appointment", kwargs={"token": appointment.finalize_token}))

        date_str = request.POST.get("date", "")
        time_str = request.POST.get("time", "")

        # 2. Timezone handling (Explicit Salon Timezone)
        try:
            tz = timezone.get_current_timezone()
            naive_dt = dt_module.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            target_dt = timezone.make_aware(naive_dt, timezone=tz)
        except ValueError:
            messages.error(request, _("Invalid date or time selected."))
            return redirect(reverse("cabinet:client_manage_appointment", kwargs={"token": appointment.finalize_token}))

        # 3. Race condition prevention: Re-verify slot availability
        from features.booking.services.cabinet_availability import CabinetBookingAvailabilityService

        availability = CabinetBookingAvailabilityService(audience="public")
        available_slots = availability.get_slots(
            booking_date=date_str,
            service_ids=[appointment.service_id],
            locked_resource_id=appointment.master_id,
        )

        if time_str not in available_slots:
            messages.error(request, _("Sorry, this slot was just taken. Please select another time."))
            return redirect(reverse("cabinet:client_manage_appointment", kwargs={"token": appointment.finalize_token}))

        appointment.datetime_start = target_dt
        appointment.save(update_fields=["datetime_start", "updated_at"])

        from features.conversations.services.notifications import _get_engine

        _get_engine().dispatch_event("booking.rescheduled", appointment)

        messages.success(request, _("Your appointment has been rescheduled."))
        return redirect(reverse("cabinet:client_manage_appointment", kwargs={"token": appointment.finalize_token}))


class ClientCancelAppointmentView(LoginRequiredMixin, View):
    """Cabinet-side cancel action — redirects back to cabinet with a message."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        appointment = get_object_or_404(Appointment, finalize_token=self.kwargs["token"])
        reason = request.POST.get("reason", Appointment.CANCEL_REASON_CLIENT)
        try:
            appointment.cancel(reason=reason)
            from features.conversations.services.notifications import _get_engine

            _get_engine().dispatch_event("booking.cancelled", appointment)
            messages.success(request, _("Your appointment has been cancelled."))
        except ValidationError:
            messages.error(request, _("This appointment cannot be cancelled."))
        return redirect(reverse("cabinet:client_appointments"))


class ClientSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "cabinet/client/settings.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_space = "client"
        request.cabinet_module = "client_settings"
        return super().dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        action = request.POST.get("action")
        user = request.user
        client: Client | None = getattr(user, "client_profile", None)
        profile: UserProfile | None = getattr(user, "profile", None)

        if action == "profile":
            if client:
                client.first_name = request.POST.get("first_name", "").strip()
                client.last_name = request.POST.get("last_name", "").strip()
                client.patronymic = request.POST.get("patronymic", "").strip()
                client.phone = request.POST.get("phone", "").strip()
                client.email = request.POST.get("email", "").strip()
                client.save(update_fields=["first_name", "last_name", "patronymic", "phone", "email", "updated_at"])

            if profile:
                profile.instagram = request.POST.get("instagram", "").strip()
                profile.telegram = request.POST.get("telegram", "").strip()
                birth_date_raw = request.POST.get("birth_date", "").strip()
                if birth_date_raw:
                    with contextlib.suppress(Exception):
                        profile.birth_date = datetime.strptime(birth_date_raw, "%Y-%m-%d").date()
                else:
                    profile.birth_date = None
                profile.save(update_fields=["instagram", "telegram", "birth_date", "updated_at"])

            messages.success(request, _("Profile updated successfully."))

        elif action == "notifications":
            if client:
                client.consent_marketing = request.POST.get("consent_marketing") == "on"
                client.consent_date = timezone.now()
                client.save(update_fields=["consent_marketing", "consent_date", "updated_at"])

            if profile:
                profile.notify_service = request.POST.get("notify_service") == "on"
                profile.notify_reminders = request.POST.get("notify_reminders") == "on"
                profile.save(update_fields=["notify_service", "notify_reminders", "updated_at"])

            messages.success(request, _("Notification preferences saved."))

        elif action == "privacy":
            if profile:
                profile.show_avatar = request.POST.get("show_avatar") == "on"
                profile.show_birth_date = request.POST.get("show_birth_date") == "on"
                profile.show_visit_history = request.POST.get("show_visit_history") == "on"
                profile.use_recommendations = request.POST.get("use_recommendations") == "on"
                profile.save(
                    update_fields=[
                        "show_avatar",
                        "show_birth_date",
                        "show_visit_history",
                        "use_recommendations",
                        "updated_at",
                    ]
                )

            if client:
                client.consent_analytics = request.POST.get("consent_analytics") == "on"
                client.save(update_fields=["consent_analytics", "updated_at"])

            messages.success(request, _("Privacy settings saved."))

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user

        client = getattr(user, "client_profile", None)
        profile = getattr(user, "profile", None)

        context.update(
            {
                "client": client,
                "profile": profile,
                "active_tab": self.request.GET.get("tab", "account"),
            }
        )
        return context

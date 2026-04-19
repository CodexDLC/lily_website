# CODEX_DJANGO_CLI BLUEPRINT STATUS: MOVE_TO_CLI_BLUEPRINT. Reason: generated app-layer or scaffold-owned file for codex-django-cli blueprints.

from __future__ import annotations

from typing import Any

from core.logger import logger
from django import forms
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView
from features.booking.booking_settings import BookingSettings
from features.booking.services.cabinet_availability import (
    CabinetBookingAvailabilityService,
    parse_resource_selections,
)

from ..mixins import StaffRequiredMixin
from ..services.booking import BookingService

BOOKING_DAY_FIELDS = {
    "monday": ("monday_is_closed", "work_start_monday", "work_end_monday"),
    "tuesday": ("tuesday_is_closed", "work_start_tuesday", "work_end_tuesday"),
    "wednesday": ("wednesday_is_closed", "work_start_wednesday", "work_end_wednesday"),
    "thursday": ("thursday_is_closed", "work_start_thursday", "work_end_thursday"),
    "friday": ("friday_is_closed", "work_start_friday", "work_end_friday"),
    "saturday": ("saturday_is_closed", "work_start_saturday", "work_end_saturday"),
    "sunday": ("sunday_is_closed", "work_start_sunday", "work_end_sunday"),
}
BOOKING_RULE_FIELDS = (
    "step_minutes",
    "default_buffer_between_minutes",
    "min_advance_minutes",
    "max_advance_days",
)
BOOKING_HOUR_FIELDS = tuple(field for fields in BOOKING_DAY_FIELDS.values() for field in fields)
BOOKING_BEHAVIOR_FIELDS = (
    "load_strategy",
    "book_only_from_next_day",
)


class BookingSettingsForm(forms.ModelForm):
    DAY_FIELDS = BOOKING_DAY_FIELDS
    SECTION_FIELDS = {
        "rules": BOOKING_RULE_FIELDS,
        "hours": BOOKING_HOUR_FIELDS,
        "behavior": BOOKING_BEHAVIOR_FIELDS,
    }

    class Meta:
        model = BookingSettings
        fields = [
            *BOOKING_RULE_FIELDS,
            *BOOKING_HOUR_FIELDS,
            *BOOKING_BEHAVIOR_FIELDS,
        ]
        widgets = {
            **{
                field: forms.TimeInput(attrs={"type": "time"})
                for fields in BOOKING_DAY_FIELDS.values()
                for field in fields[1:]
            },
            "load_strategy": forms.Select(),
            "book_only_from_next_day": forms.CheckboxInput(),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            else:
                base_class = "form-control"
                if isinstance(widget, forms.TimeInput):
                    base_class += " form-control-sm"
                widget.attrs["class"] = base_class

    @property
    def grouped_fields(self) -> dict[str, list[forms.BoundField]]:
        return {section: [self[name] for name in field_names] for section, field_names in self.SECTION_FIELDS.items()}

    @property
    def day_rows(self) -> list[dict[str, forms.BoundField | str]]:
        labels = {
            "monday": _("Monday"),
            "tuesday": _("Tuesday"),
            "wednesday": _("Wednesday"),
            "thursday": _("Thursday"),
            "friday": _("Friday"),
            "saturday": _("Saturday"),
            "sunday": _("Sunday"),
        }
        return [
            {
                "key": day,
                "label": labels[day],
                "closed": self[fields[0]],
                "start": self[fields[1]],
                "end": self[fields[2]],
            }
            for day, fields in self.DAY_FIELDS.items()
        ]


class BaseBookingView(StaffRequiredMixin, TemplateView):
    """Base class for staff-only booking cabinet views."""

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_module = "booking"
        return super().dispatch(request, *args, **kwargs)


class BookingScheduleView(BaseBookingView):
    """Renders the calendar/schedule."""

    template_name = "cabinet/booking/schedule.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(BookingService.get_schedule_context(self.request))
        return context


class NewBookingView(BaseBookingView):
    """Renders the form/dashboard for creating a new booking."""

    template_name = "cabinet/booking/new.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(BookingService.get_new_booking_context(self.request))
        return context


class BookingCreateView(BaseBookingView):
    """POST endpoint for the cabinet full booking builder."""

    def post(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        result = BookingService.create_new_booking(request)
        return redirect(result["target_url"])


class BookingListView(BaseBookingView):
    """Renders appointment lists with status filtering."""

    template_name = "cabinet/booking/list.html"

    def get_template_names(self) -> list[str]:
        if self.request.headers.get("HX-Request"):
            return ["cabinet/booking/partials/_appointments_table.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        status = self.kwargs.get("status") or self.request.GET.get("status", "all")

        list_context = BookingService.get_list_context(self.request, status=status)
        context.update(list_context)
        context["current_status"] = status
        return context


class BookingModalView(BaseBookingView):
    """Renders modular modals for a specific booking."""

    template_name = "cabinet/components/generic_modal.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        booking_id = self.kwargs.get("pk")
        context.update(BookingService.get_booking_modal_context(self.request, booking_id))
        return context


class BookingActionView(BaseBookingView):
    """Thin POST endpoint for demo booking actions."""

    def post(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        result = BookingService.perform_action(
            request,
            booking_id=self.kwargs["pk"],
            action=self.kwargs["action"],
        )
        return redirect(result["target_url"])


class BookingSettingsView(BaseBookingView):
    """Render and save resource-slot booking settings for the booking module."""

    template_name = "cabinet/booking/settings.html"

    def _load_settings(self) -> tuple[BookingSettings, str | None]:
        instance, warning = BookingService.get_or_create_settings()
        return instance, _(warning) if warning else None  # type: ignore[arg-type]

    def _get_context(self, *, form: BookingSettingsForm, storage_warning: str | None) -> dict[str, Any]:
        context = self.get_context_data()
        context.update(
            {
                "title": _("Booking settings"),
                "form": form,
                "form_sections": form.grouped_fields,
                "storage_warning": storage_warning,
            }
        )
        return context

    def get(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        instance, storage_warning = self._load_settings()
        form = BookingSettingsForm(instance=instance)
        return self.render_to_response(self._get_context(form=form, storage_warning=storage_warning))

    def post(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        instance, storage_warning = self._load_settings()
        if storage_warning:
            messages.error(request, storage_warning)
            form = BookingSettingsForm(instance=instance)
            return self.render_to_response(self._get_context(form=form, storage_warning=storage_warning))

        form = BookingSettingsForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, _("Booking settings saved."))
            return redirect("cabinet:booking_settings")

        return self.render_to_response(self._get_context(form=form, storage_warning=storage_warning))


# ── Appointment Group views ───────────────────────────────────────────────────


class BookingGroupListView(StaffRequiredMixin, TemplateView):
    """List of AppointmentGroup records — same-day multi-service bookings."""

    template_name = "cabinet/booking/group_list.html"

    def get(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        from features.booking.models import AppointmentGroup

        status_filter = request.GET.get("status", "")
        qs = (
            AppointmentGroup.objects.select_related("client")
            .prefetch_related("items__appointment__service")
            .order_by("-created_at")
        )
        if status_filter:
            qs = qs.filter(status=status_filter)

        context = self.get_context_data()
        context.update(
            {
                "groups": qs[:200],
                "status_filter": status_filter,
                "status_choices": AppointmentGroup.STATUS_CHOICES,
            }
        )

        if request.headers.get("HX-Request"):
            return self.response_class(
                request=request,
                template=["cabinet/booking/partials/_group_table.html"],
                context=context,
            )
        return self.render_to_response(context)


class BookingGroupActionView(StaffRequiredMixin, TemplateView):
    """Perform bulk actions on an AppointmentGroup."""

    template_name = "cabinet/booking/group_list.html"

    def post(self, request: Any, pk: int, action: str, **kwargs: Any) -> HttpResponse:
        from features.booking.models import AppointmentGroup

        group = get_object_or_404(AppointmentGroup, pk=pk)

        if action == "confirm_all":
            group.confirm_all()
        elif action == "cancel_all":
            reason = request.POST.get("reason", "other")
            note = request.POST.get("note", "")
            group.cancel_all(reason=reason, note=note)

        if request.headers.get("HX-Request"):
            response = HttpResponse(status=200)
            response["HX-Redirect"] = "/cabinet/booking/groups/"
            return response


class BookingSlotFetchView(StaffRequiredMixin, View):
    """AJAX endpoint to fetch smart slots for cabinet wizard."""

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        date_str = request.GET.get("date", "")
        service_ids_str = request.GET.get("service_ids", "")
        master_id_str = request.GET.get("master_id", "")
        resource_selections_raw = request.GET.get("master_selections", "")

        service_ids = [int(i) for i in service_ids_str.split(",") if i.isdigit()]
        master_id = int(master_id_str) if master_id_str and master_id_str.isdigit() else 0
        resource_selections = parse_resource_selections(resource_selections_raw)

        if not date_str or not service_ids:
            return JsonResponse({"slots": [], "date": date_str, "service_ids": service_ids})

        availability = CabinetBookingAvailabilityService()
        slots = availability.get_slots(
            booking_date=date_str,
            service_ids=service_ids,
            locked_resource_id=master_id or None,
            resource_selections=resource_selections,
        )
        logger.debug(
            "Cabinet slot fetch completed: date={} service_ids={} resource_id={} resource_selections={} slots={}",
            date_str,
            service_ids,
            master_id or None,
            resource_selections,
            slots,
        )
        return JsonResponse(
            {
                "slots": slots,
                "date": date_str,
                "service_ids": service_ids,
                "master_id": master_id or None,
            }
        )


class BookingDayFetchView(StaffRequiredMixin, View):
    """AJAX endpoint to fetch available booking dates for the selected services."""

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        from django.utils import timezone

        service_ids_str = request.GET.get("service_ids", "")
        master_id_str = request.GET.get("master_id", "")
        resource_selections_raw = request.GET.get("master_selections", "")

        service_ids = [int(i) for i in service_ids_str.split(",") if i.isdigit()]
        master_id = int(master_id_str) if master_id_str and master_id_str.isdigit() else 0
        resource_selections = parse_resource_selections(resource_selections_raw)

        if not service_ids:
            return JsonResponse({"available_dates": [], "first_available_date": ""})

        availability = CabinetBookingAvailabilityService()
        settings = BookingSettings.load()
        start_date = timezone.localdate()

        available_dates = sorted(
            availability.get_available_dates(
                start_date=start_date,
                horizon=settings.max_advance_days,
                service_ids=service_ids,
                locked_resource_id=master_id or None,
                resource_selections=resource_selections,
            )
        )
        logger.debug(
            "Cabinet day fetch completed: service_ids={} resource_id={} resource_selections={} available_dates={}",
            service_ids,
            master_id or None,
            resource_selections,
            available_dates,
        )
        return JsonResponse(
            {
                "available_dates": available_dates,
                "first_available_date": available_dates[0] if available_dates else "",
            }
        )

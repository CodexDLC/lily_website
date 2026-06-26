from typing import Any

from django import forms
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, UpdateView
from features.booking.booking_settings import BookingSettings
from features.booking.models.master import Master
from features.booking.models.schedule import MasterWorkingDay

from cabinet.mixins import StaffRequiredMixin
from cabinet.services.staff import StaffService


class MasterQuickEditForm(forms.ModelForm):
    WEEKDAY_CHOICES = [
        ("0", "Mo"),
        ("1", "Tu"),
        ("2", "We"),
        ("3", "Th"),
        ("4", "Fr"),
        ("5", "Sa"),
        ("6", "Su"),
    ]

    work_days = forms.MultipleChoiceField(
        required=False,
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Master
        fields = ["name", "title", "status", "order", "is_public", "years_experience", "work_days"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
            "is_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "years_experience": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["work_days"].initial = [str(day) for day in self.instance.work_days]

    def save(self, commit: bool = True) -> Master:
        selected_days = sorted({int(day) for day in self.cleaned_data.get("work_days", [])})
        instance = super().save(commit=False)
        if commit:
            with transaction.atomic():
                instance.save()
                self._sync_working_days(instance, selected_days)
        return instance

    @staticmethod
    def _sync_working_days(master: Master, selected_days: list[int]) -> None:
        settings = BookingSettings.load()
        existing = {item.weekday: item for item in master.working_days.all()}

        for weekday, item in existing.items():
            if weekday not in selected_days:
                item.delete()

        for weekday in selected_days:
            booking_day_schedule = settings.get_day_schedule(weekday)
            start_time = booking_day_schedule[0] if booking_day_schedule is not None else None
            end_time = booking_day_schedule[1] if booking_day_schedule is not None else None
            defaults = {
                "start_time": master.work_start or start_time,
                "end_time": master.work_end or end_time,
                "break_start": master.break_start,
                "break_end": master.break_end,
            }
            if defaults["start_time"] and defaults["end_time"]:
                MasterWorkingDay.objects.update_or_create(
                    master=master,
                    weekday=weekday,
                    defaults=defaults,
                )


class StaffListView(StaffRequiredMixin, TemplateView):
    template_name = "cabinet/staff/list.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_module = "staff"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(StaffService.get_list_context(self.request))
        return context


class StaffDaysOffView(StaffRequiredMixin, TemplateView):
    template_name = "cabinet/staff/days_off.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_module = "staff"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            StaffService.get_days_off_context(
                self.request,
                master_id=self._get_int(self.request.GET.get("master_id")),
                year=self._get_int(self.request.GET.get("year")),
                month=self._get_int(self.request.GET.get("month")),
            )
        )
        return context

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        master_id = self._get_int(request.POST.get("master_id"))
        year = self._get_int(request.POST.get("year"))
        month = self._get_int(request.POST.get("month"))
        if master_id is None or year is None or month is None:
            messages.error(request, _("Please select a master and month."))
            return redirect("cabinet:staff_days_off")

        result = StaffService.save_days_off(
            master_id=master_id,
            year=year,
            month=month,
            selected_dates=request.POST.getlist("dates"),
        )
        blocked_dates = result["blocked_dates"]
        if blocked_dates:
            messages.warning(
                request,
                _("Some days were not closed because they already have active appointments."),
            )
        messages.success(request, _("Days off saved."))
        query = urlencode({"master_id": master_id, "year": year, "month": month})
        return redirect(f"{reverse('cabinet:staff_days_off')}?{query}")

    @staticmethod
    def _get_int(value: str | None) -> int | None:
        if not value:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


class StaffQuickEditView(StaffRequiredMixin, UpdateView):
    model = Master
    form_class = MasterQuickEditForm
    template_name = "cabinet/staff/includes/quick_edit_form.html"

    def form_valid(self, form: Any) -> Any:
        self.object = form.save()
        return JsonResponse({"status": "ok", "message": "Staff member updated successfully", "refresh": True})

    def form_invalid(self, form: Any) -> Any:
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)

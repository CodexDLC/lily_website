"""Masters list view (Admin only)."""

from django.http import JsonResponse
from django.views.generic import TemplateView
from features.booking.models import Master
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin

WORKDAYS_CHOICES = [
    (0, "Пн"),
    (1, "Вт"),
    (2, "Ср"),
    (3, "Чт"),
    (4, "Пт"),
    (5, "Сб"),
    (6, "Вс"),
]


class MastersView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/masters/list.html"

    ALLOWED_STATUSES = {
        Master.STATUS_ACTIVE,
        Master.STATUS_VACATION,
        Master.STATUS_FIRED,
        Master.STATUS_TRAINING,
    }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "masters"
        ctx["masters"] = Master.objects.order_by("order", "name")
        ctx["workdays_choices"] = WORKDAYS_CHOICES
        return ctx

    def post(self, request, *args, **kwargs):
        master_id = request.POST.get("master_id")
        try:
            master = Master.objects.get(pk=master_id)
        except Master.DoesNotExist:
            return JsonResponse({"ok": False, "error": "not found"}, status=404)

        status = request.POST.get("status")
        if status in self.ALLOWED_STATUSES:
            master.status = status

        master.phone = request.POST.get("phone", "").strip()

        raw_days = request.POST.getlist("work_days")
        days = sorted({int(d) for d in raw_days if d.isdigit() and 0 <= int(d) <= 6})
        master.work_days = days

        master.is_public = request.POST.get("is_public") == "1"

        master.save(update_fields=["status", "phone", "work_days", "is_public"])
        return JsonResponse({"ok": True, "status_display": master.get_status_display()})

"""Masters list view (Admin only)."""

from core.logger import log
from django.http import JsonResponse
from django.views.generic import TemplateView
from features.booking.models import Master
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin

# Weekdays mapping for display in the cabinet
WORKDAYS_CHOICES = [
    (0, "Mo"),
    (1, "Tu"),
    (2, "We"),
    (3, "Th"),
    (4, "Fr"),
    (5, "Sa"),
    (6, "Su"),
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
        log.debug(f"View: MastersView | Action: GetContext | user={self.request.user.id}")
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "masters"
        ctx["masters"] = Master.objects.order_by("order", "name")
        ctx["workdays_choices"] = WORKDAYS_CHOICES
        return ctx

    def post(self, request, *args, **kwargs):
        master_id = request.POST.get("master_id")
        log.info(f"View: MastersView | Action: UpdateMaster | master_id={master_id} | user={request.user.id}")

        try:
            master = Master.objects.get(pk=master_id)
        except Master.DoesNotExist:
            log.error(f"View: MastersView | Action: UpdateFailed | master_id={master_id} | error=NotFound")
            return JsonResponse({"ok": False, "error": "not found"}, status=404)

        status = request.POST.get("status")
        if status in self.ALLOWED_STATUSES:
            master.status = status
            log.debug(f"View: MastersView | Action: ChangeStatus | master_id={master_id} | status={status}")

        master.phone = request.POST.get("phone", "").strip()

        raw_days = request.POST.getlist("work_days")
        days = sorted({int(d) for d in raw_days if d.isdigit() and 0 <= int(d) <= 6})
        master.work_days = days
        log.debug(f"View: MastersView | Action: ChangeWorkDays | master_id={master_id} | days={days}")

        master.is_public = request.POST.get("is_public") == "1"

        try:
            master.save(update_fields=["status", "phone", "work_days", "is_public"])
            log.info(f"View: MastersView | Action: Success | master_id={master_id}")
        except Exception as e:
            log.error(f"View: MastersView | Action: SaveFailed | master_id={master_id} | error={e}")
            return JsonResponse({"ok": False, "error": str(e)}, status=500)

        return JsonResponse({"ok": True, "status_display": master.get_status_display()})

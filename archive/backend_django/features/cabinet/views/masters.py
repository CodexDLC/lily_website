"""Masters CRM view (Admin only)."""

from core.logger import log
from django.shortcuts import get_object_or_404, render
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
    template_name = "cabinet/crm/masters/list.html"

    def dispatch(self, request, *args, **kwargs):
        # Handle HTMX actions (edit, save, view)
        action = request.POST.get("action") or request.GET.get("action")
        master_id = request.POST.get("id") or request.GET.get("id")

        if action and master_id:
            master = get_object_or_404(Master, id=master_id)

            if action == "edit":
                return render(
                    request,
                    "cabinet/crm/masters/_edit_form.html",
                    {"master": master, "workdays_choices": WORKDAYS_CHOICES},
                )

            if action == "view":
                return render(
                    request,
                    "cabinet/crm/masters/_single_card.html",
                    {"master": master, "workdays_choices": WORKDAYS_CHOICES},
                )

        if request.method == "POST" and action == "save" and master_id:
            master = get_object_or_404(Master, id=master_id)

            # Update basic fields
            master.name = request.POST.get("name", "").strip()
            master.title = request.POST.get("title", "").strip()
            master.phone = request.POST.get("phone", "").strip()
            master.instagram = request.POST.get("instagram", "").strip()
            master.status = request.POST.get("status", Master.STATUS_ACTIVE)
            master.is_public = request.POST.get("is_public") == "on"

            # Update work days
            raw_days = request.POST.getlist("work_days")
            days = sorted({int(d) for d in raw_days if d.isdigit() and 0 <= int(d) <= 6})
            master.work_days = days

            master.save()
            log.info(f"CRM: Master {master.id} updated by user {request.user.id}")
            return render(
                request,
                "cabinet/crm/masters/_single_card.html",
                {"master": master, "workdays_choices": WORKDAYS_CHOICES},
            )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        log.debug(f"View: MastersView | Action: GetContext | user={self.request.user.id}")
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "masters"

        # Filtering
        show_fired = self.request.GET.get("show_fired") == "1"
        status_filter = self.request.GET.get("status")

        qs = Master.objects.order_by("order", "name")

        if not show_fired:
            qs = qs.exclude(status=Master.STATUS_FIRED)

        if status_filter:
            qs = qs.filter(status=status_filter)

        ctx["masters"] = qs
        ctx["show_fired"] = show_fired
        ctx["status_filter"] = status_filter
        ctx["workdays_choices"] = WORKDAYS_CHOICES
        ctx["status_choices"] = Master.STATUS_CHOICES

        return ctx

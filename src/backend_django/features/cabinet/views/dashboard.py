"""Admin dashboard view with key statistics."""

from datetime import timedelta

from core.logger import log
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin


class DashboardView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/dashboard/index.html"

    def get_context_data(self, **kwargs):
        log.debug(f"View: DashboardView | Action: GetContext | user={self.request.user.id}")
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "dashboard"
        from features.booking.models import Appointment, Client

        today = timezone.localdate()
        month_start = today.replace(day=1)
        week_ago = today - timedelta(days=7)

        # Statistics
        ctx["today_confirmed"] = Appointment.objects.filter(
            datetime_start__date=today, status=Appointment.STATUS_CONFIRMED
        ).count()
        ctx["pending_count"] = Appointment.objects.filter(status=Appointment.STATUS_PENDING).count()
        ctx["month_revenue"] = (
            Appointment.objects.filter(
                status=Appointment.STATUS_COMPLETED,
                datetime_start__date__gte=month_start,
            ).aggregate(total=Sum("price"))["total"]
            or 0
        )
        ctx["total_clients_count"] = Client.objects.count()
        ctx["new_clients_week"] = Client.objects.filter(created_at__date__gte=week_ago).count()

        # Upcoming appointments today
        ctx["today_appointments"] = (
            Appointment.objects.filter(datetime_start__date=today)
            .exclude(status=Appointment.STATUS_CANCELLED)
            .select_related("client", "master", "service")
            .order_by("datetime_start")
        )

        log.info(
            f"View: DashboardView | Action: Success | pending={ctx['pending_count']} | today_confirmed={ctx['today_confirmed']}"
        )
        return ctx

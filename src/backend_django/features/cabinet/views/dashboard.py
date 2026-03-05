"""Admin dashboard view with key statistics."""

from datetime import timedelta

from core.logger import log
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.views.generic import TemplateView
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin


class DashboardView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/crm/dashboard/index.html"

    def get_context_data(self, **kwargs):
        log.debug(f"View: DashboardView | Action: GetContext | user={self.request.user.id}")
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "dashboard"
        from features.booking.models import Appointment, Client, Master
        from features.main.models.service import Service

        today = timezone.localdate()
        month_start = today.replace(day=1)
        week_ago = today - timedelta(days=7)

        # Statistics
        ctx["today_confirmed"] = Appointment.objects.filter(
            datetime_start__date=today, status=Appointment.STATUS_CONFIRMED
        ).count()
        ctx["today_total_count"] = (
            Appointment.objects.filter(datetime_start__date=today).exclude(status=Appointment.STATUS_CANCELLED).count()
        )

        ctx["pending_count"] = Appointment.objects.filter(status=Appointment.STATUS_PENDING).count()

        # New totals
        ctx["total_confirmed"] = Appointment.objects.filter(status=Appointment.STATUS_CONFIRMED).count()
        ctx["total_completed"] = Appointment.objects.filter(status=Appointment.STATUS_COMPLETED).count()

        # Revenue
        ctx["month_revenue"] = (
            Appointment.objects.filter(
                status=Appointment.STATUS_COMPLETED,
                datetime_start__date__gte=month_start,
            ).aggregate(total=Sum("price"))["total"]
            or 0
        )
        ctx["total_revenue_lifetime"] = (
            Appointment.objects.filter(status=Appointment.STATUS_COMPLETED).aggregate(total=Sum("price"))["total"] or 0
        )

        # Clients
        ctx["total_clients_count"] = Client.objects.count()
        ctx["new_clients_week"] = Client.objects.filter(created_at__date__gte=week_ago).count()

        # Masters Stats (All active masters)
        masters_stats = (
            Master.objects.filter(status=Master.STATUS_ACTIVE)
            .annotate(
                month_appointments=Count(
                    "appointments",
                    filter=Q(
                        appointments__status=Appointment.STATUS_COMPLETED,
                        appointments__datetime_start__date__gte=month_start,
                    ),
                ),
                month_revenue=Sum(
                    "appointments__price",
                    filter=Q(
                        appointments__status=Appointment.STATUS_COMPLETED,
                        appointments__datetime_start__date__gte=month_start,
                    ),
                ),
            )
            .order_by("-month_appointments")
        )
        ctx["masters_stats"] = masters_stats

        # Services Stats
        ctx["services_total"] = Service.objects.count()
        ctx["services_active"] = Service.objects.filter(is_active=True).count()
        ctx["services_disabled"] = ctx["services_total"] - ctx["services_active"]

        # Top Services by Revenue (This Month)
        top_services = (
            Service.objects.filter(is_active=True)
            .annotate(
                month_revenue=Sum(
                    "appointments__price",
                    filter=Q(
                        appointments__status=Appointment.STATUS_COMPLETED,
                        appointments__datetime_start__date__gte=month_start,
                    ),
                ),
                month_count=Count(
                    "appointments",
                    filter=Q(
                        appointments__status=Appointment.STATUS_COMPLETED,
                        appointments__datetime_start__date__gte=month_start,
                    ),
                ),
            )
            .filter(month_count__gt=0)
            .order_by("-month_revenue")[:10]  # Top 10
        )
        ctx["top_services"] = top_services

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

"""Dashboard context selector with Redis caching."""

from datetime import timedelta

from core.cache import get_cached_data
from core.logger import log
from django.db.models import Count, Q, Sum
from django.utils import timezone

DASHBOARD_CACHE_KEY = "dashboard_context_cache"
_DASHBOARD_CACHE_TTL = 5 * 60  # 5 minutes safety net


def get_dashboard_context() -> dict:
    return get_cached_data(DASHBOARD_CACHE_KEY, _fetch_dashboard_data, timeout=_DASHBOARD_CACHE_TTL)


def _fetch_dashboard_data() -> dict:
    log.debug("Selector: DashboardSelector | Action: FetchDashboardData")

    from features.booking.models import Appointment, Client, Master
    from features.main.models.service import Service

    today = timezone.localdate()
    month_start = today.replace(day=1)
    week_ago = today - timedelta(days=7)

    today_confirmed = Appointment.objects.filter(
        datetime_start__date=today, status=Appointment.STATUS_CONFIRMED
    ).count()

    today_total_count = (
        Appointment.objects.filter(datetime_start__date=today).exclude(status=Appointment.STATUS_CANCELLED).count()
    )

    pending_count = Appointment.objects.filter(status=Appointment.STATUS_PENDING).count()

    total_confirmed = Appointment.objects.filter(status=Appointment.STATUS_CONFIRMED).count()
    total_completed = Appointment.objects.filter(status=Appointment.STATUS_COMPLETED).count()

    month_revenue = (
        Appointment.objects.filter(
            status=Appointment.STATUS_COMPLETED,
            datetime_start__date__gte=month_start,
        ).aggregate(total=Sum("price"))["total"]
        or 0
    )
    total_revenue_lifetime = (
        Appointment.objects.filter(status=Appointment.STATUS_COMPLETED).aggregate(total=Sum("price"))["total"] or 0
    )

    total_clients_count = Client.objects.count()
    new_clients_week = Client.objects.filter(created_at__date__gte=week_ago).count()

    masters_stats = list(
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

    services_total = Service.objects.count()
    services_active = Service.objects.filter(is_active=True).count()

    top_services = list(
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
        .order_by("-month_revenue")[:10]
    )

    today_appointments = list(
        Appointment.objects.filter(datetime_start__date=today)
        .exclude(status=Appointment.STATUS_CANCELLED)
        .select_related("client", "master", "service")
        .order_by("datetime_start")
    )

    log.debug("Selector: DashboardSelector | Action: Success")

    return {
        "today_confirmed": today_confirmed,
        "today_total_count": today_total_count,
        "pending_count": pending_count,
        "total_confirmed": total_confirmed,
        "total_completed": total_completed,
        "month_revenue": month_revenue,
        "total_revenue_lifetime": total_revenue_lifetime,
        "total_clients_count": total_clients_count,
        "new_clients_week": new_clients_week,
        "masters_stats": masters_stats,
        "services_total": services_total,
        "services_active": services_active,
        "services_disabled": services_total - services_active,
        "top_services": top_services,
        "today_appointments": today_appointments,
    }

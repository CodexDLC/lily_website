from typing import Any

from codex_django.cabinet.views import dashboard_view
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.views.generic import TemplateView

from ..mixins import StaffRequiredMixin
from ..services.reports import LilyReportsService

_staff_check = user_passes_test(lambda u: u.is_active and (u.is_staff or u.is_superuser))


@_staff_check
def analytics_dashboard_view(request: Any) -> HttpResponse:
    """Wrapper for analytics dashboard to set active module."""
    request.cabinet_module = "business_stats"
    return dashboard_view(request)


class AnalyticsReportsView(StaffRequiredMixin, TemplateView):
    """Detailed analytics reports page."""

    template_name = "cabinet/reports/page.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_module = "business_stats"
        request.cabinet_space = "staff"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["report"] = LilyReportsService.build(self.request)
        return context

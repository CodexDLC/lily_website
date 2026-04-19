"""Admin dashboard view with key statistics."""

from core.logger import log
from django.views.generic import TemplateView
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin
from features.cabinet.selector.dashboard_selector import get_dashboard_context


class DashboardView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/crm/dashboard/index.html"

    def get_context_data(self, **kwargs):
        log.debug(f"View: DashboardView | Action: GetContext | user={self.request.user.id}")
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "dashboard"
        ctx.update(get_dashboard_context())
        log.info(
            f"View: DashboardView | Action: Success | pending={ctx['pending_count']} | today_confirmed={ctx['today_confirmed']}"
        )
        return ctx

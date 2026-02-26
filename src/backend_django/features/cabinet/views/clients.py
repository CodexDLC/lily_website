"""Clients CRM view (Admin only)."""

from datetime import timedelta

from core.logger import log
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.generic import TemplateView
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin


class ClientsView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/clients/list.html"

    def get_context_data(self, **kwargs):
        log.debug(f"View: ClientsView | Action: GetContext | user={self.request.user.id}")
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "clients"
        from features.booking.models import Client

        search = self.request.GET.get("q", "").strip()
        period = self.request.GET.get("period", "")

        log.debug(f"View: ClientsView | Action: Filtering | search='{search}' | period={period}")

        qs = Client.objects.order_by("-created_at")

        if search:
            from django.db.models import Q

            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
            )

        if period == "week":
            week_ago = timezone.localdate() - timedelta(days=7)
            qs = qs.filter(created_at__date__gte=week_ago)

        paginator = Paginator(qs, 25)
        page_num = self.request.GET.get("page", 1)
        ctx["page_obj"] = paginator.get_page(page_num)
        ctx["search"] = search
        ctx["period"] = period

        log.info(f"View: ClientsView | Action: Success | total_found={paginator.count} | page={page_num}")
        return ctx

"""Clients CRM view (Admin only)."""

from django.core.paginator import Paginator
from django.views.generic import TemplateView
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin


class ClientsView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/clients/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "clients"
        from features.booking.models import Client

        search = self.request.GET.get("q", "").strip()
        qs = Client.objects.order_by("-created_at")

        if search:
            from django.db.models import Q

            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
            )

        paginator = Paginator(qs, 25)
        page_num = self.request.GET.get("page", 1)
        ctx["page_obj"] = paginator.get_page(page_num)
        ctx["search"] = search
        return ctx

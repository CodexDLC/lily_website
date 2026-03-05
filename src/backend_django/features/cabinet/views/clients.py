"""Clients CRM view (Admin only)."""

from datetime import timedelta

from core.logger import log
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import TemplateView
from features.booking.models import Client
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin


class ClientsView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/crm/clients/list.html"

    def dispatch(self, request, *args, **kwargs):
        # Handle HTMX actions (edit, save, view)
        action = request.GET.get("action")
        client_id = request.GET.get("id")

        if action and client_id:
            client = get_object_or_404(Client, id=client_id)

            if action == "edit":
                return render(request, "cabinet/crm/clients/_edit_form.html", {"client": client})

            if action == "view":
                # Return just the single card content (wrapped in its ID for swap)
                return render(request, "cabinet/crm/clients/_single_card.html", {"client": client})

        if request.method == "POST" and action == "save" and client_id:
            client = get_object_or_404(Client, id=client_id)
            client.first_name = request.POST.get("first_name", "").strip()
            client.last_name = request.POST.get("last_name", "").strip()
            client.phone = request.POST.get("phone", "").strip()
            client.email = request.POST.get("email", "").strip()
            client.instagram = request.POST.get("instagram", "").strip()
            client.telegram = request.POST.get("telegram", "").strip()
            client.notes = request.POST.get("notes", "").strip()
            client.save()
            log.info(f"CRM: Client {client.id} updated by user {request.user.id}")
            return render(request, "cabinet/crm/clients/_single_card.html", {"client": client})

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        log.debug(f"View: ClientsView | Action: GetContext | user={self.request.user.id}")
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "clients"

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

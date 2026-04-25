from __future__ import annotations

from typing import Any

from asgiref.sync import async_to_sync
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView, DetailView, ListView, View
from django.views.generic.edit import CreateView
from features.conversations.campaigns.audience import AudienceFilter
from features.conversations.forms.campaign import CampaignForm
from features.conversations.models.campaign import Campaign, CampaignRecipient
from features.conversations.services.campaign_service import build_campaign_service

from cabinet.mixins import StaffRequiredMixin


class CampaignListView(StaffRequiredMixin, ListView):
    template_name = "cabinet/campaigns/list.html"
    context_object_name = "campaigns"
    paginate_by = 30

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_module = "conversations"
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Campaign.objects.all()


class CampaignCreateView(StaffRequiredMixin, CreateView):
    template_name = "cabinet/campaigns/compose.html"
    form_class = CampaignForm

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_module = "conversations"
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        audience_filter = form.get_audience_filter()
        campaign = form.save(commit=False)
        campaign.created_by = self.request.user
        campaign.locale = "de"
        campaign.audience_filter = audience_filter.to_dict()

        action = self.request.POST.get("action", "draft")

        if action == "send":
            campaign.save()
            service = build_campaign_service()
            try:
                async_to_sync(service.send)(campaign)
                messages.success(self.request, _("Campaign queued for sending."))
            except Exception as exc:
                messages.error(self.request, f"Failed to enqueue campaign: {exc}")
        else:
            campaign.status = Campaign.Status.DRAFT
            campaign.save()
            messages.success(self.request, _("Campaign saved as draft."))

        return redirect("cabinet:conversations_campaigns_detail", pk=campaign.pk)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class CampaignDetailView(StaffRequiredMixin, DetailView):
    template_name = "cabinet/campaigns/detail.html"
    context_object_name = "campaign"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_module = "conversations"
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Campaign.objects.all()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        campaign = self.object
        status_counts = {
            status: campaign.recipients.filter(status=status).count() for status, _ in CampaignRecipient.Status.choices
        }
        context["status_counts"] = status_counts
        context["recipients"] = campaign.recipients.order_by("id")[:100]
        return context


class CampaignDeleteView(StaffRequiredMixin, DeleteView):
    model = Campaign
    success_url = reverse_lazy("cabinet:conversations_campaigns")

    def get(self, request, *args, **kwargs):
        """Skip confirmation page, just delete on GET if requested via HTMX or simple link,
        but let's stick to POST for safety if not using HTMX."""
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        campaign = self.get_object()
        if campaign.status == Campaign.Status.SENDING:
            messages.error(request, _("Cannot delete a campaign while it is sending."))
            return redirect("cabinet:conversations_campaigns_detail", pk=campaign.pk)

        campaign.delete()
        messages.success(request, _("Campaign deleted successfully."))
        return redirect(self.success_url)


class AudienceCountView(StaffRequiredMixin, View):
    """HTMX endpoint — returns JSON recipient count for the current filter."""

    def get(self, request, *args, **kwargs):
        from datetime import date

        appointment_since_raw = request.GET.get("audience_has_appointment_since")
        is_marketing_raw = request.GET.get("is_marketing")
        form_sent = request.GET.get("campaign_form_sent") == "1"

        is_marketing = is_marketing_raw == "on" if form_sent else True

        appointment_since = None
        if appointment_since_raw:
            import contextlib

            with contextlib.suppress(ValueError):
                appointment_since = date.fromisoformat(appointment_since_raw)

        f = AudienceFilter(
            email_opt_in=is_marketing,
            has_valid_email=True,
            has_appointment_since=appointment_since,
        )
        service = build_campaign_service()
        count = service.preview_count(f)
        return HttpResponse(str(count), content_type="text/plain")

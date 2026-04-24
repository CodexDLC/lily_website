from __future__ import annotations

from typing import TYPE_CHECKING

from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.generic import View

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


class UnsubscribeView(View):
    """
    Public unsubscribe view — no login required.
    GET  → confirmation page
    POST → sets consent_marketing=False, email_opt_out_at=now()
    """

    template_name = "features/conversations/unsubscribe.html"

    def _get_client(self, token: str):
        from system.models import Client

        try:
            return Client.objects.get(unsubscribe_token=token)
        except Client.DoesNotExist:
            return None

    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        client = self._get_client(str(token))
        if client is None:
            return TemplateResponse(request, self.template_name, {"not_found": True})
        if client.email_opt_out_at is not None:
            return TemplateResponse(request, self.template_name, {"already_done": True})
        return TemplateResponse(request, self.template_name, {})

    def post(self, request: HttpRequest, token: str) -> HttpResponse:
        client = self._get_client(str(token))
        if client is None:
            return TemplateResponse(request, self.template_name, {"not_found": True})

        if client.email_opt_out_at is None:
            client.consent_marketing = False
            client.email_opt_out_at = timezone.now()
            client.save(update_fields=["consent_marketing", "email_opt_out_at", "updated_at"])

        return TemplateResponse(request, self.template_name, {"success": True})

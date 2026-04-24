from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import apps
from django.conf import settings
from django.db.models import Q, QuerySet

from features.conversations.campaigns.audience import AudienceFilter, RecipientDraft

if TYPE_CHECKING:
    from collections.abc import Iterable


def _get_client_model():
    return apps.get_model(settings.CONVERSATIONS_RECIPIENT_MODEL)


class DjangoAudienceBuilder:
    """Materialises AudienceFilter into a QuerySet of the configured recipient model."""

    def _queryset(self, f: AudienceFilter) -> QuerySet:
        client_model = _get_client_model()
        qs = client_model.objects.all()

        if f.email_opt_in:
            qs = qs.filter(consent_marketing=True)

        if f.has_valid_email:
            qs = qs.exclude(Q(email__isnull=True) | Q(email=""))

        # Exclude already opted-out
        qs = qs.filter(email_opt_out_at__isnull=True)

        if f.locales:
            # Client has no per-client locale yet — skip locale filtering for now
            pass

        if f.has_appointment_since:
            qs = qs.filter(appointments__start_time__date__gte=f.has_appointment_since).distinct()

        if f.service_ids:
            qs = qs.filter(appointments__service_id__in=f.service_ids).distinct()

        return qs

    def count(self, f: AudienceFilter) -> int:
        return self._queryset(f).count()

    def materialize(self, f: AudienceFilter) -> Iterable[RecipientDraft]:
        for client in self._queryset(f).iterator(chunk_size=500):
            if not client.email:
                continue
            yield RecipientDraft(
                recipient_id=client.pk,
                email=client.email,
                first_name=client.first_name or "",
                last_name=client.last_name or "",
                locale="de",
                unsubscribe_token=str(client.unsubscribe_token),
            )

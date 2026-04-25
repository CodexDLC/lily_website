from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from datetime import date

from features.conversations.campaigns.audience import AudienceFilter
from features.conversations.campaigns.templates import template_registry
from features.conversations.models.campaign import Campaign


class CampaignForm(forms.ModelForm):
    audience_has_appointment_since = forms.DateField(
        label=_("Clients with appointment since"),
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = Campaign
        fields = ["subject", "is_marketing", "body_text", "template_key"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Email subject")}),
            "body_text": forms.Textarea(attrs={"class": "form-control", "rows": 10}),
            "template_key": forms.Select(attrs={"class": "form-select"}),
            "is_marketing": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["template_key"].widget = forms.Select(
            choices=template_registry.choices_for_locale("de"),
            attrs={"class": "form-select"},
        )
        self.fields["template_key"].choices = template_registry.choices_for_locale("de")
        self.fields["is_marketing"].initial = True

    def get_audience_filter(self) -> AudienceFilter:
        since: date | None = self.cleaned_data.get("audience_has_appointment_since")
        is_marketing = self.cleaned_data.get("is_marketing", True)
        return AudienceFilter(
            email_opt_in=is_marketing,
            has_valid_email=True,
            has_appointment_since=since,
        )

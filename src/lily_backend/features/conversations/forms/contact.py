from typing import ClassVar

from django import forms
from django.utils.translation import gettext_lazy as _

from ..models import Message


class ContactForm(forms.ModelForm):
    # Non-model consent fields (not stored, just validated)
    dsgvo_consent = forms.BooleanField(
        label=_(
            'Ich habe die <a href="/datenschutz/" target="_blank" rel="noopener noreferrer"'
            ' style="color: var(--color-gold); text-decoration: underline;">Datenschutzerklärung</a>'
            " gelesen und erkläre mich mit der Verarbeitung meiner Daten einverstanden."
        ),
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "checkbox-custom"}),
    )
    consent_marketing = forms.BooleanField(
        label=_("Ich möchte über Neuigkeiten und Angebote informiert werden."),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "checkbox-custom"}),
    )

    class Meta:
        model = Message
        fields: ClassVar[list[str]] = ["sender_name", "sender_email", "sender_phone", "topic", "body"]
        labels: ClassVar[dict[str, str]] = {
            "sender_name": _("Name"),
            "sender_email": _("E-Mail"),
            "sender_phone": _("Telefon (optional)"),
            "topic": _("Thema"),
            "body": _("Nachricht"),
        }
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "sender_name": forms.TextInput(
                attrs={
                    "class": "input-line",
                    "placeholder": _("Vor- und Nachname"),
                    "autocomplete": "name",
                }
            ),
            "sender_email": forms.EmailInput(
                attrs={
                    "class": "input-line",
                    "placeholder": _("ihre@email.de"),
                    "autocomplete": "email",
                }
            ),
            "sender_phone": forms.TextInput(
                attrs={
                    "class": "input-line",
                    "placeholder": _("+49 …"),
                    "autocomplete": "tel",
                }
            ),
            "topic": forms.Select(attrs={"class": "input-line"}),
            "body": forms.Textarea(
                attrs={
                    "class": "input-line",
                    "rows": 4,
                    "placeholder": _("Ihre Nachricht..."),
                }
            ),
        }

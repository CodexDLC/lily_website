from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

from .models import ContactRequest


class ContactForm(forms.Form):
    CONTACT_TYPES = [
        ("phone", _("Telefon / WhatsApp")),
        ("email", _("E-Mail")),
    ]

    first_name = forms.CharField(
        label=_("Vorname"),
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "input-line",
                "placeholder": _("Vorname"),
                "autocomplete": "given-name",
            }
        ),
    )

    last_name = forms.CharField(
        label=_("Nachname"),
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "input-line",
                "placeholder": _("Nachname"),
                "autocomplete": "family-name",
            }
        ),
    )

    contact_type = forms.ChoiceField(
        choices=CONTACT_TYPES, widget=forms.Select(attrs={"class": "input-line"}), label=_("Kontaktart")
    )

    contact_value = forms.CharField(
        label=_("Kontakt"),
        widget=forms.TextInput(
            attrs={
                "class": "input-line",
                "placeholder": _("Nummer oder E-Mail"),
                "autocomplete": "tel",
            }
        ),
    )

    topic = forms.ChoiceField(
        label=_("Thema"), choices=ContactRequest.TOPIC_CHOICES, widget=forms.Select(attrs={"class": "input-line"})
    )

    message = forms.CharField(
        label=_("Nachricht"),
        widget=forms.Textarea(attrs={"class": "input-line", "rows": 4, "placeholder": _("Ihre Nachricht...")}),
        required=False,
    )

    dsgvo_consent = forms.BooleanField(
        label=_(
            'Ich habe die <a href="/datenschutz/" target="_blank" rel="noopener noreferrer" style="color: var(--color-gold); text-decoration: underline;">Datenschutzerklärung</a> gelesen und erkläre mich mit der Verarbeitung meiner Daten einverstanden.'
        ),
        required=True,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "checkbox-custom"}),
    )

    consent_marketing = forms.BooleanField(
        label=_("Ich möchte über Neuigkeiten und Angebote informiert werden."),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "checkbox-custom", "checked": "checked"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        c_type = cleaned_data.get("contact_type")
        c_value = cleaned_data.get("contact_value")

        if c_type == "email" and c_value:
            try:
                validate_email(c_value)
            except ValidationError:
                self.add_error("contact_value", _("Bitte geben Sie eine gültige E-Mail-Adresse ein."))

        return cleaned_data

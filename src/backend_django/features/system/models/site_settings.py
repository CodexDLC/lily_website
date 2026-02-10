from django.db import models
from django.utils.translation import gettext_lazy as _


class SiteSettings(models.Model):
    """
    Singleton model for global site settings (Contacts, Socials, Legal info).
    """

    # --- General ---
    company_name = models.CharField(_("Company Name"), max_length=255, default="LILY Beauty Salon")
    owner_name = models.CharField(_("Owner Name"), max_length=255, default="Liliia Yakina")
    tax_number = models.CharField(_("Tax Number (Steuernummer)"), max_length=100, blank=True)

    # --- Contacts ---
    phone = models.CharField(_("Phone"), max_length=50, default="+49 176 59423704")
    email = models.EmailField(_("Email"), default="info@lily-salon.de")
    address_street = models.CharField(_("Street"), max_length=255, default="Lohmannstraße 111")
    address_city = models.CharField(_("City & ZIP"), max_length=255, default="06366 Köthen (Anhalt)")
    google_maps_link = models.URLField(_("Google Maps Link"), blank=True, help_text="Link to open location in Maps")

    # --- Socials ---
    instagram_url = models.URLField(_("Instagram URL"), blank=True, default="https://instagram.com/manikure_kothen")
    telegram_url = models.URLField(_("Telegram URL"), blank=True)
    whatsapp_url = models.URLField(_("WhatsApp URL"), blank=True)

    # --- Working Hours ---
    working_hours_weekdays = models.CharField(_("Mo-Fr"), max_length=100, default="09:00 - 18:00")
    working_hours_saturday = models.CharField(_("Saturday"), max_length=100, default="10:00 - 14:00")
    working_hours_sunday = models.CharField(_("Sunday"), max_length=100, default="Geschlossen")

    class Meta:
        verbose_name = _("Site Settings")
        verbose_name_plural = _("Site Settings")

    def __str__(self):
        return "Global Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

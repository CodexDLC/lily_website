from datetime import time
from decimal import Decimal

from django.conf import settings
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
    site_base_url = models.URLField(
        _("Site Base URL"), blank=True, help_text=_("If empty, uses value from .env (SITE_BASE_URL)")
    )
    logo_url = models.CharField(
        _("Logo URL"),
        max_length=500,
        blank=True,
        default="/static/img/logo_lily.webp",
        help_text=_("Can be an absolute URL or a relative static path."),
    )

    # --- Contacts ---
    phone = models.CharField(_("Phone"), max_length=50, default="+49 176 59423704")
    email = models.EmailField(_("Email"), default="info@lily-salon.de")
    address_street = models.CharField(_("Street"), max_length=255, default="Lohmannstraße 111")
    address_locality = models.CharField(_("City"), max_length=255, default="Köthen (Anhalt)")
    address_postal_code = models.CharField(_("PLZ"), max_length=10, default="06366")
    google_maps_link = models.URLField(_("Google Maps Link"), blank=True, help_text="Link to open location in Maps")
    latitude = models.DecimalField(_("Latitude"), max_digits=9, decimal_places=6, default="51.746495")
    longitude = models.DecimalField(_("Longitude"), max_digits=9, decimal_places=6, default="11.9784666")

    # --- Socials ---
    instagram_url = models.URLField(_("Instagram URL"), blank=True, default="https://instagram.com/manikure_kothen")
    telegram_url = models.URLField(_("Telegram URL"), blank=True)
    whatsapp_url = models.URLField(_("WhatsApp URL"), blank=True)
    facebook_url = models.URLField(_("Facebook URL"), blank=True)
    telegram_bot_username = models.CharField(
        _("Telegram Bot Username"),
        max_length=100,
        blank=True,
        default="codexen_test_bot",
        help_text=_("Username of the bot without @ (e.g., lily_beauty_bot)"),
    )

    # --- Working Hours (Display Strings) ---
    working_hours_weekdays = models.CharField(_("Mo-Fr (Display)"), max_length=100, default="09:00 - 18:00")
    working_hours_saturday = models.CharField(_("Saturday (Display)"), max_length=100, default="10:00 - 14:00")
    working_hours_sunday = models.CharField(_("Sunday (Display)"), max_length=100, default="Geschlossen")

    # --- Working Hours (Logic) ---
    # Mo-Fr
    work_start_weekdays = models.TimeField(_("Mo-Fr Start"), default=time(9, 0))
    work_end_weekdays = models.TimeField(_("Mo-Fr End"), default=time(18, 0))

    # Saturday
    work_start_saturday = models.TimeField(_("Saturday Start"), default=time(10, 0))
    work_end_saturday = models.TimeField(_("Saturday End"), default=time(14, 0))

    # Sunday is closed by default logic

    # --- Price Range ---
    price_range = models.CharField(_("Price Range"), max_length=10, default="$$")

    # --- Technical URL Paths ---
    url_path_contact_form = models.CharField(_("Contact Form URL Path"), max_length=255, default="/contacts/")
    url_path_confirm = models.CharField(
        _("Booking Confirm URL Path"), max_length=255, default="/appointments/confirm/{token}/"
    )
    url_path_cancel = models.CharField(
        _("Booking Cancel URL Path"), max_length=255, default="/appointments/cancel/{token}/"
    )
    url_path_reschedule = models.CharField(_("Booking Reschedule URL Path"), max_length=255, default="/booking/")

    # --- Hiring / Vacancies ---
    hiring_active = models.BooleanField(
        _("Hiring Active"), default=True, help_text="Show 'We are hiring' block on Team page"
    )
    hiring_title = models.CharField(_("Hiring Title"), max_length=255, default="Wir suchen Verstärkung!", blank=True)
    hiring_text = models.TextField(
        _("Hiring Text"), blank=True, default="Bist du talentiert und liebst deinen Job? Werde Teil unseres Teams!"
    )

    # --- Analytics & Marketing ---
    google_analytics_id = models.CharField(
        _("Google Analytics ID"),
        max_length=50,
        blank=True,
        help_text=_("GA4 Measurement ID (e.g., G-XXXXXXXXXX)"),
    )
    google_tag_manager_id = models.CharField(
        _("Google Tag Manager ID"),
        max_length=50,
        blank=True,
        help_text=_("GTM Container ID (e.g., GTM-XXXXXXX)"),
    )

    class Meta:
        verbose_name = _("Site Settings")
        verbose_name_plural = _("Site Settings")

    def __str__(self):
        return "Global Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1

        # Sync with .env if field is empty
        if not self.site_base_url:
            self.site_base_url = settings.SITE_BASE_URL

        super().save(*args, **kwargs)

        # Сохраняем настройки        # Sync to Redis for the Bot
        from features.system.redis_managers.site_settings_manager import SiteSettingsManager

        SiteSettingsManager.save_to_redis(self)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def to_dict(self) -> dict:
        """
        Возвращает словарь со всеми значимыми полями модели для кэширования.
        """
        data = {}
        for field in self._meta.get_fields():
            if field.concrete and not field.many_to_many and not field.one_to_many:
                value = getattr(self, field.name)

                # Fallback for site_base_url if it's somehow empty in DB
                if field.name == "site_base_url" and not value:
                    value = settings.SITE_BASE_URL

                if isinstance(value, time):
                    data[field.name] = value.strftime("%H:%M")
                elif isinstance(value, Decimal):
                    data[field.name] = str(value)
                else:
                    data[field.name] = value
        return data

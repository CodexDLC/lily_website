from codex_django.system.mixins.settings import (
    AbstractSiteSettings,
    SiteContactSettingsMixin,
    SiteEmailIdentityMixin,
    SiteGeoSettingsMixin,
    SiteMarketingSettingsMixin,
    SiteSocialSettingsMixin,
    SiteTechnicalSettingsMixin,
)
from django.db import models
from django.utils.translation import gettext_lazy as _


class SiteSettings(
    AbstractSiteSettings,
    SiteContactSettingsMixin,
    SiteGeoSettingsMixin,
    SiteSocialSettingsMixin,
    SiteMarketingSettingsMixin,
    SiteTechnicalSettingsMixin,
    SiteEmailIdentityMixin,
):
    """
    Global site settings.
    Automatically synchronized with Redis.
    """

    # --- General ---
    company_name = models.CharField(_("Company Name"), max_length=255, default="LILY Beauty Salon")
    owner_name = models.CharField(_("Owner Name"), max_length=255, blank=True)
    tax_number = models.CharField(_("Tax Number (Steuernummer)"), max_length=100, blank=True)
    site_base_url = models.URLField(_("Site Base URL"), blank=True)
    logo_url = models.CharField(
        _("Logo URL"),
        max_length=500,
        blank=True,
        default="/static/img/logo_lily.webp",
    )

    # --- Telegram Bot ---
    telegram_bot_username = models.CharField(
        _("Telegram Bot Username"),
        max_length=100,
        blank=True,
        help_text=_("Username without @ (e.g., lily_beauty_bot)"),
    )

    # --- Working Hours (Display Strings) ---
    working_hours_weekdays = models.CharField(_("Mo-Fr (Display)"), max_length=100, blank=True, default="09:00 - 18:00")
    working_hours_saturday = models.CharField(
        _("Saturday (Display)"), max_length=100, blank=True, default="10:00 - 14:00"
    )
    working_hours_sunday = models.CharField(_("Sunday (Display)"), max_length=100, blank=True, default="Geschlossen")

    # --- Price ---
    price_range = models.CharField(_("Price Range"), max_length=10, blank=True, default="$$")

    # --- Technical URL Paths ---
    url_path_contact_form = models.CharField(_("Contact Form URL Path"), max_length=255, default="/contacts/")
    url_path_confirm = models.CharField(
        _("Booking Confirm URL Path"), max_length=255, default="/appointments/confirm/{token}/"
    )
    url_path_cancel = models.CharField(
        _("Booking Cancel URL Path"), max_length=255, default="/appointments/cancel/{token}/"
    )
    url_path_reschedule = models.CharField(
        _("Booking Reschedule URL Path"), max_length=255, default="/cabinet/appointments/reschedule/{token}/"
    )

    # --- Hiring ---
    hiring_active = models.BooleanField(
        _("Hiring Active"), default=True, help_text=_("Show 'We are hiring' block on Team page")
    )
    hiring_title = models.CharField(_("Hiring Title"), max_length=255, blank=True, default="Wir suchen Verstärkung!")
    hiring_text = models.TextField(
        _("Hiring Text"), blank=True, default="Bist du talentiert und liebst deinen Job? Werde Teil unseres Teams!"
    )

    @classmethod
    def load(cls):
        """
        Singleton load method.
        Gets existing instance with pk=1 or creates a new one.
        """
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def to_dict(self):
        """
        Returns a dictionary representation of the settings.
        Simplified to rely on base class logic for JSON serialization.
        """
        return super().to_dict()

    class Meta:
        verbose_name = _("Настройки сайта")
        verbose_name_plural = _("Настройки сайта")


def get_site_settings_manager():
    """
    Returns the appropriate manager for synchronizing SiteSettings with Redis.
    Uses the library manager from codex_django.
    """
    try:
        from codex_django.core.redis.managers.settings import DjangoSiteSettingsManager

        return DjangoSiteSettingsManager()
    except ImportError:
        # Fallback or Mock if library is not available (e.g. in some environments)
        class MockManager:
            def save_instance(self, instance):
                pass

        return MockManager()

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from ..models.settings import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    """
    Admin for site settings.
    Only one record is expected (Singleton pattern).
    """

    list_display = ("company_name", "phone", "email", "social_status")
    list_display_links = ("company_name",)

    fieldsets = (
        (
            _("General Information"),
            {
                "fields": (
                    "company_name",
                    "owner_name",
                    "tax_number",
                    "site_base_url",
                    "logo_url",
                    "price_range",
                    "telegram_bot_username",
                ),
            },
        ),
        (
            _("Contact Details"),
            {
                "fields": (
                    "phone",
                    "email",
                    "address_street",
                    "address_locality",
                    "address_postal_code",
                    "contact_person",
                ),
            },
        ),
        (
            _("Geo Data"),
            {
                "fields": ("google_maps_link", "latitude", "longitude"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Social Media"),
            {
                "fields": (
                    "instagram_url",
                    "facebook_url",
                    "telegram_url",
                    "whatsapp_url",
                    "youtube_url",
                    "linkedin_url",
                    "tiktok_url",
                    "twitter_url",
                    "pinterest_url",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Working Hours"),
            {
                "fields": (
                    "working_hours_weekdays",
                    "working_hours_saturday",
                    "working_hours_sunday",
                    "work_start_weekdays",
                    "work_end_weekdays",
                    "work_start_saturday",
                    "work_end_saturday",
                ),
            },
        ),
        (
            _("Marketing & Analytics"),
            {
                "fields": (
                    "google_analytics_id",
                    "google_tag_manager_id",
                    "facebook_pixel_id",
                    "tiktok_pixel_id",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Technical Settings"),
            {
                "fields": ("app_mode_enabled", "maintenance_mode", "head_scripts", "body_scripts"),
            },
        ),
        (
            _("Email (SMTP)"),
            {
                "fields": (
                    "smtp_host",
                    "smtp_port",
                    "smtp_user",
                    "smtp_password",
                    "smtp_from_email",
                    "smtp_use_tls",
                    "smtp_use_ssl",
                    "sendgrid_api_key",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Hiring / Vacancies"),
            {
                "fields": ("hiring_active", "hiring_title", "hiring_text"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Technical URL Paths"),
            {
                "fields": (
                    "url_path_contact_form",
                    "url_path_confirm",
                    "url_path_cancel",
                    "url_path_reschedule",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_("Social Media"))
    def social_status(self, obj):
        socials = [obj.instagram_url, obj.facebook_url, obj.telegram_url, obj.whatsapp_url]
        count = sum(1 for s in socials if s)

        if count == 4:
            color_classes = "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400"
            label = f"✓ All ({count}/4)"
        elif count > 0:
            color_classes = "bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400"
            label = f"⚠ {count}/4"
        else:
            color_classes = "bg-gray-100 text-gray-700 dark:bg-gray-500/20 dark:text-gray-400"
            label = "✗ None"

        return format_html(
            '<span class="px-2 py-1 rounded-md text-xs font-medium {}">{}</span>',
            color_classes,
            label,
        )

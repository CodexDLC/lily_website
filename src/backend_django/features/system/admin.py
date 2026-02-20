"""Admin interface for system app using Unfold."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin

from .models import SiteSettings, StaticPageSeo


@admin.register(StaticPageSeo)
class StaticPageSeoAdmin(ModelAdmin, TranslationAdmin):
    """Admin interface for StaticPageSeo model."""

    list_display = ["page_key", "title_preview", "has_description", "has_image"]
    list_display_links = ["page_key"]
    list_filter = ["page_key"]
    search_fields = ["page_key", "seo_title", "seo_description"]

    # SEO Optimization at the TOP
    fieldsets = [
        (
            _("SEO Optimization"),
            {"fields": ("seo_title", "seo_description", "seo_image")},
        ),
        (
            _("Page Identification"),
            {"fields": ("page_key",)},
        ),
    ]

    @admin.display(description=_("SEO Title"))
    def title_preview(self, obj):
        title = obj.seo_title or "—"
        length = len(obj.seo_title) if obj.seo_title else 0

        if 50 <= length <= 60:
            color_class = "text-green-600 dark:text-green-400"
        elif length > 0:
            color_class = "text-orange-600 dark:text-orange-400"
        else:
            color_class = "text-gray-400"

        return format_html(
            '<span class="font-bold {}">{}</span> <small class="opacity-50">({} chars)</small>',
            mark_safe(color_class),
            title[:50] + "..." if len(title) > 50 else title,
            length,
        )

    @admin.display(description=_("Description"))
    def has_description(self, obj):
        if obj.seo_description:
            length = len(obj.seo_description)
            color_classes = mark_safe("bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400")
            return format_html(
                '<span class="px-2 py-1 rounded-md text-xs font-medium {}">✓ {} chars</span>',
                color_classes,
                length,
            )
        return format_html('<span class="text-gray-400 text-xs">✗ No description</span>')

    @admin.display(description=_("OG Image"))
    def has_image(self, obj):
        if obj.seo_image:
            color_classes = mark_safe("bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400")
            return format_html('<span class="px-2 py-1 rounded-md text-xs font-medium {}">✓ Yes</span>', color_classes)
        return format_html('<span class="text-gray-400 text-xs">✗ No</span>')


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    """Admin interface for SiteSettings model."""

    list_display = ["company_name", "phone", "email", "social_status"]
    list_display_links = ["company_name"]

    fieldsets = [
        (
            _("General Information"),
            {"fields": ("company_name", "owner_name", "tax_number")},
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
                    "google_maps_link",
                )
            },
        ),
        (
            _("Social Media"),
            {"fields": ("instagram_url", "telegram_url", "whatsapp_url", "telegram_bot_username")},
        ),
        (
            _("Working Hours"),
            {
                "fields": (
                    "working_hours_weekdays",
                    "working_hours_saturday",
                    "working_hours_sunday",
                )
            },
        ),
        (
            _("Analytics & Marketing"),
            {
                "fields": ("google_analytics_id", "google_tag_manager_id"),
                "description": _("Configure Google Analytics 4 and Tag Manager. Changes take effect immediately."),
            },
        ),
    ]

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_("Social Media"))
    def social_status(self, obj):
        socials = [obj.instagram_url, obj.telegram_url, obj.whatsapp_url]
        count = sum(1 for s in socials if s)

        if count == 3:
            color_classes = mark_safe("bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400")
            label = f"✓ All ({count}/3)"
        elif count > 0:
            color_classes = mark_safe("bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400")
            label = f"⚠ {count}/3"
        else:
            color_classes = mark_safe("bg-gray-100 text-gray-700 dark:bg-gray-500/20 dark:text-gray-400")
            label = "✗ None"

        return format_html(
            '<span class="px-2 py-1 rounded-md text-xs font-medium {}">{}</span>',
            color_classes,
            label,
        )

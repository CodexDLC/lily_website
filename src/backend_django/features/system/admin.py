"""Admin interface for system app."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from .models import SiteSettings, StaticPageSeo

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN CLASSES
# ══════════════════════════════════════════════════════════════════════════════


@admin.register(StaticPageSeo)
class StaticPageSeoAdmin(TranslationAdmin):
    """Admin interface for StaticPageSeo model."""

    list_display = ["page_key", "title_preview", "has_description", "has_image"]
    list_filter = ["page_key"]
    search_fields = ["page_key", "seo_title", "seo_description"]

    fieldsets = [
        (
            _("Page Identification"),
            {"fields": ("page_key",)},
        ),
        (
            _("SEO Meta Tags"),
            {"fields": ("seo_title", "seo_description")},
        ),
        (
            _("Open Graph Image"),
            {"fields": ("seo_image",)},
        ),
    ]

    @admin.display(description=_("SEO Title"))
    def title_preview(self, obj):
        """Show SEO title with character count."""
        title = obj.seo_title or "—"
        length = len(obj.seo_title) if obj.seo_title else 0
        color = "green" if 50 <= length <= 60 else "orange" if length > 0 else "gray"
        return format_html(
            '<strong style="color:{};">{}</strong> <small>({} chars)</small>',
            color,
            title[:50] + "..." if len(title) > 50 else title,
            length,
        )

    @admin.display(description=_("Description"))
    def has_description(self, obj):
        """Check if SEO description exists."""
        if obj.seo_description:
            length = len(obj.seo_description)
            color = "green" if 150 <= length <= 160 else "orange"
            return format_html(
                '<span style="padding:3px 8px;background:{};color:white;border-radius:3px;">✓ {} chars</span>',
                color,
                length,
            )
        return format_html(
            '<span style="padding:3px 8px;background:gray;color:white;border-radius:3px;">✗ {}</span>',
            _("No description"),
        )

    @admin.display(description=_("OG Image"))
    def has_image(self, obj):
        """Check if OG image exists."""
        if obj.seo_image:
            return format_html(
                '<span style="padding:3px 8px;background:green;color:white;border-radius:3px;">✓ {}</span>',
                _("Yes"),
            )
        return format_html(
            '<span style="padding:3px 8px;background:gray;color:white;border-radius:3px;">✗ {}</span>',
            _("No"),
        )


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for SiteSettings model.
    Singleton pattern - only one instance allowed.
    """

    list_display = ["company_name", "phone", "email", "has_socials"]

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
            {"fields": ("instagram_url", "telegram_url", "whatsapp_url")},
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
    ]

    def has_add_permission(self, request):
        """Allow add only if no instance exists (Singleton pattern)."""
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of site settings."""
        return False

    @admin.display(description=_("Social Media"))
    def has_socials(self, obj):
        """Check if social media links are configured."""
        socials = [obj.instagram_url, obj.telegram_url, obj.whatsapp_url]
        count = sum(1 for s in socials if s)

        if count == 3:
            return format_html(
                '<span style="padding:3px 8px;background:green;color:white;border-radius:3px;">✓ All ({}/3)</span>',
                count,
            )
        elif count > 0:
            return format_html(
                '<span style="padding:3px 8px;background:orange;color:white;border-radius:3px;">⚠ {}/3</span>',
                count,
            )
        return format_html(
            '<span style="padding:3px 8px;background:gray;color:white;border-radius:3px;">✗ None</span>',
        )

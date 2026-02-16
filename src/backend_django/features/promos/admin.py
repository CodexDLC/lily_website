"""Admin interface for promos app using Unfold."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin
from unfold.decorators import action

from .models import PromoMessage


@admin.register(PromoMessage)
class PromoMessageAdmin(ModelAdmin, TranslationAdmin):
    """Admin interface for PromoMessage model."""

    list_display = [
        "title",
        "status_badge",
        "priority",
        "button_preview",
        "statistics_display",
        "date_range_display",
    ]
    list_display_links = ["title"]
    list_filter = ["is_active", "starts_at", "ends_at", "priority"]
    search_fields = ["title", "description", "button_text"]
    readonly_fields = ["views_count", "clicks_count", "calculated_ctr", "created_at", "updated_at"]
    date_hierarchy = "starts_at"

    fieldsets = [
        (
            _("Content"),
            {
                "fields": (
                    "title",
                    "description",
                    "button_text",
                    "image",
                )
            },
        ),
        (
            _("Scheduling"),
            {
                "fields": (
                    "is_active",
                    "starts_at",
                    "ends_at",
                    "display_delay",
                    "priority",
                )
            },
        ),
        (
            _("Targeting"),
            {
                "fields": ("target_pages",),
                "description": _("Leave empty to show on all pages. Use comma-separated slugs (e.g., 'home,services')"),
            },
        ),
        (
            _("Design"),
            {
                "fields": (
                    "button_color",
                    "text_color",
                )
            },
        ),
        (
            _("Statistics"),
            {
                "fields": (
                    "views_count",
                    "clicks_count",
                    "calculated_ctr",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    ]

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        """Display colored status badge."""
        status = obj.status_display

        colors = {
            _("Active"): "bg-green-100 text-green-700",
            _("Scheduled"): "bg-blue-100 text-blue-700",
            _("Expired"): "bg-red-100 text-red-700",
            _("Inactive"): "bg-gray-100 text-gray-700",
        }

        icons = {
            _("Active"): "✓",
            _("Scheduled"): "⏰",
            _("Expired"): "⏹",
            _("Inactive"): "•",
        }

        color_classes = mark_safe(colors.get(status, "bg-gray-100 text-gray-700"))
        icon = icons.get(status, "•")

        return format_html(
            '<span class="px-2 py-1 rounded-md text-xs font-medium {}">{} {}</span>',
            color_classes,
            icon,
            status,
        )

    @admin.display(description=_("Button Preview"))
    def button_preview(self, obj):
        """Show preview of how the button will look."""
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 4px 8px; border-radius: 10px; font-size: 10px;">{}</span>',
            obj.button_color,
            obj.text_color,
            obj.button_text,
        )

    @admin.display(description=_("Statistics"))
    def statistics_display(self, obj):
        """Show views and clicks statistics in list view."""
        if obj.views_count == 0:
            return _("No views yet")

        ctr_value = f"{obj.ctr:.1f}%"
        return format_html(
            "👁 {} | 🖱 {} | CTR: {}",
            obj.views_count,
            obj.clicks_count,
            ctr_value,
        )

    @admin.display(description=_("Date Range"))
    def date_range_display(self, obj):
        """Show formatted date range in list view."""
        if not obj.starts_at or not obj.ends_at:
            return "—"
        return f"{obj.starts_at.strftime('%Y-%m-%d')} - {obj.ends_at.strftime('%Y-%m-%d')}"

    @admin.display(description=_("CTR"))
    def calculated_ctr(self, obj):
        """Display click-through rate in detail view."""
        if obj.views_count == 0:
            return "—"
        return f"{obj.ctr:.2f}%"

    @action(description=_("Activate selected promos"))
    def activate_promos(self, request, queryset):
        """Activate selected promos."""
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f"{updated} notification(s) activated."))

    @action(description=_("Deactivate selected promos"))
    def deactivate_promos(self, request, queryset):
        """Deactivate selected promos."""
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f"{updated} notification(s) deactivated."))

    actions = ["activate_promos", "deactivate_promos"]

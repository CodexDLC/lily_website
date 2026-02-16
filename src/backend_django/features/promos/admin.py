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
        "statistics",
        "date_range",
    ]
    list_display_links = ["title"]
    list_filter = ["is_active", "starts_at", "ends_at", "priority"]
    search_fields = ["title", "description", "button_text"]
    readonly_fields = ["views_count", "clicks_count", "ctr_display", "created_at", "updated_at"]
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
                    "ctr_display",
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

        if status == str(_("Active")):
            color_classes = "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400"
            icon = "✓"
        elif status == str(_("Scheduled")):
            color_classes = "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400"
            icon = "⏰"
        elif status == str(_("Expired")):
            color_classes = "bg-gray-100 text-gray-700 dark:bg-gray-500/20 dark:text-gray-400"
            icon = "⏹"
        else:  # Inactive
            color_classes = "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400"
            icon = "✗"

        return format_html(
            '<span class="px-2 py-1 rounded-md text-xs font-medium {}">{} {}</span>',
            color_classes,
            icon,
            status,
        )

    @admin.display(description=_("Button Preview"))
    def button_preview(self, obj):
        """Show preview of how the button will look."""
        style = f"background-color: {obj.button_color}; color: {obj.text_color}; padding: 6px 12px; border-radius: 15px; font-size: 11px; display: inline-block;"
        return format_html('<span style="{}">{}</span>', mark_safe(style), obj.button_text)

    @admin.display(description=_("Statistics"))
    def statistics(self, obj):
        """Show views and clicks statistics."""
        if obj.views_count == 0:
            return format_html('<span class="text-gray-400 text-xs">No views yet</span>')

        ctr = float(obj.ctr)
        if ctr >= 10:
            color_class = "text-green-600 dark:text-green-400"
        elif ctr >= 5:
            color_class = "text-orange-600 dark:text-orange-400"
        else:
            color_class = "text-gray-600 dark:text-gray-400"

        return format_html(
            '<span class="text-xs {}">👁 {} | 🖱 {} | CTR: {:.1f}%</span>',
            color_class,
            obj.views_count,
            obj.clicks_count,
            ctr,
        )

    @admin.display(description=_("Date Range"))
    def date_range(self, obj):
        """Show formatted date range."""
        start = obj.starts_at.strftime("%Y-%m-%d %H:%M")
        end = obj.ends_at.strftime("%Y-%m-%d %H:%M")
        return format_html('<span class="text-xs">{} → {}</span>', start, end)

    @admin.display(description=_("CTR"))
    def ctr_display(self, obj):
        """Display click-through rate."""
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

    def get_queryset(self, request):
        """Optimize query with select_related/prefetch_related if needed."""
        qs = super().get_queryset(request)
        return qs

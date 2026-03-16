from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from features.promos.models import PromoMessage
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin


@admin.register(PromoMessage)
class PromoMessageAdmin(TabbedTranslationAdmin, ModelAdmin):
    list_display = ["title", "status_badge", "starts_at", "ends_at", "is_active", "priority"]
    list_filter = ["is_active", "starts_at", "ends_at"]
    search_fields = ["title", "description"]
    save_on_top = True

    fieldsets = (
        (
            _("Content"),
            {"fields": ("title", "description", "button_text", "image")},
        ),
        (
            _("Schedule"),
            {"fields": ("starts_at", "ends_at", "is_active")},
        ),
        (
            _("Display & Targeting"),
            {"fields": ("priority", "display_delay", "target_pages", "button_color", "text_color")},
        ),
        (
            _("Analytics"),
            {"fields": ("views_count", "clicks_count"), "classes": ("collapse",)},
        ),
    )

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        # Convert lazy proxy to string for comparison
        status_text = str(obj.status_display)

        # Color mapping based on translated status text
        # Includes common translations for reliability
        colors = {
            "Active": "bg-green-500/20 text-green-700 dark:text-green-400",
            "Активно": "bg-green-500/20 text-green-700 dark:text-green-400",
            "Aktiv": "bg-green-500/20 text-green-700 dark:text-green-400",
            "Scheduled": "bg-yellow-500/20 text-yellow-700 dark:text-yellow-400",
            "Запланировано": "bg-yellow-500/20 text-yellow-700 dark:text-yellow-400",
            "Geplant": "bg-yellow-500/20 text-yellow-700 dark:text-yellow-400",
            "Expired": "bg-red-500/20 text-red-700 dark:text-red-400",
            "Истекло": "bg-red-500/20 text-red-700 dark:text-red-400",
            "Abgelaufen": "bg-red-500/20 text-red-700 dark:text-red-400",
            "Inactive": "bg-gray-500/20 text-gray-700 dark:text-gray-400",
            "Неактивно": "bg-gray-500/20 text-gray-700 dark:text-gray-400",
            "Inaktiv": "bg-gray-500/20 text-gray-700 dark:text-gray-400",
        }

        color = colors.get(status_text, "bg-gray-500/20 text-gray-600")

        return format_html('<span class="px-2 py-1 rounded-md text-xs font-medium {}">{}</span>', color, status_text)

    def get_queryset(self, request):
        """Optimize queryset and set default ordering."""
        return super().get_queryset(request).order_by("-priority", "-starts_at")

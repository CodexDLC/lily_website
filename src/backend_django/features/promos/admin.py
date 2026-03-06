from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from features.promos.models import PromoMessage
from unfold.admin import ModelAdmin


@admin.register(PromoMessage)
class PromoMessageAdmin(ModelAdmin):
    list_display = ("title", "status_badge", "starts_at", "ends_at", "is_active")
    list_filter = ("is_active", "starts_at", "ends_at")
    search_fields = ("title", "description")
    save_on_top = True

    fieldsets = (
        (
            _("Content"),
            {"fields": ("title", "description", "image")},
        ),
        (
            _("Schedule"),
            {"fields": ("starts_at", "ends_at", "is_active")},
        ),
        (
            _("Display Options"),
            {"fields": ("priority", "display_delay", "button_text", "button_color", "text_color")},
        ),
    )

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        status = obj.status_display

        if status == _("Inactive"):
            color = "bg-gray-500/20 text-gray-700 dark:text-gray-400"
        elif status == _("Active"):
            color = "bg-green-500/20 text-green-700 dark:text-green-400"
        elif status == _("Scheduled"):
            color = "bg-yellow-500/20 text-yellow-700 dark:text-yellow-400"
        else:
            color = "bg-red-500/20 text-red-700 dark:text-red-400"

        # Admin-only status coloring
        # nosec B308,B703
        return mark_safe(f'<span class="px-2 py-1 rounded-md text-xs font-medium {color}">{status}</span>')

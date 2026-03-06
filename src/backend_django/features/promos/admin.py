from django.contrib import admin
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from features.promos.models import PromoMessage
from unfold.admin import ModelAdmin


@admin.register(PromoMessage)
class PromoMessageAdmin(ModelAdmin):
    list_display = ("title", "category", "status_badge", "start_date", "end_date", "is_active")
    list_filter = ("is_active", "category", "start_date", "end_date")
    search_fields = ("title", "text")
    save_on_top = True

    fieldsets = (
        (
            _("Content"),
            {"fields": ("title", "text", "image", "category")},
        ),
        (
            _("Schedule"),
            {"fields": ("start_date", "end_date", "is_active")},
        ),
        (
            _("Display Options"),
            {"fields": ("priority", "show_in_bot", "show_on_website")},
        ),
    )

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        if not obj.is_active:
            color = "bg-gray-500/20 text-gray-700 dark:text-gray-400"
            text = _("Inactive")
        elif obj.is_now_active:
            color = "bg-green-500/20 text-green-700 dark:text-green-400"
            text = _("Active Now")
        else:
            color = "bg-yellow-500/20 text-yellow-700 dark:text-yellow-400"
            text = _("Scheduled")

        # Admin-only status coloring
        # nosec B308,B703
        return mark_safe(f'<span class="px-2 py-1 rounded-md text-xs font-medium {color}">{text}</span>')

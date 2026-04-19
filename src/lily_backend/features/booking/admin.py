from django.contrib import admin
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin, TabularInline

from .booking_settings import BookingSettings
from .models import (
    Appointment,
    AppointmentGroup,
    AppointmentGroupItem,
    Master,
    MasterDayOff,
    MasterWorkingDay,
)


class MasterWorkingDayInline(TabularInline):
    model = MasterWorkingDay
    extra = 0


class MasterDayOffInline(TabularInline):
    model = MasterDayOff
    extra = 0


@admin.register(Master)
class MasterAdmin(TranslationAdmin, ModelAdmin):
    list_display = ["name", "status_badge", "is_owner", "is_public", "order", "telegram_username"]
    list_display_links = ["name"]
    list_editable = ["order", "is_public", "is_owner"]
    list_filter = ("status", "is_public", "is_owner", "categories")
    search_fields = ("name", "telegram_username", "phone")
    prepopulated_fields = {"slug": ["name"]}
    readonly_fields = ("bot_access_code", "qr_token")
    inlines = [MasterWorkingDayInline, MasterDayOffInline]

    fieldsets = (
        (
            _("Basic Info"),
            {
                "fields": (
                    "name",
                    "slug",
                    "photo",
                    "title",
                    "short_description",
                    "bio",
                ),
            },
        ),
        (
            _("Status & Visibility"),
            {
                "fields": ("status", "is_public", "is_owner", "is_featured", "order", "booking_priority"),
            },
        ),
        (
            _("Working Hours"),
            {
                "fields": (
                    "work_start",
                    "work_end",
                    "break_start",
                    "break_end",
                ),
            },
        ),
        (
            _("Booking Constraints"),
            {
                "fields": (
                    "buffer_between_minutes",
                    "min_advance_minutes",
                    "max_advance_days",
                    "max_clients_parallel",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Professional"),
            {
                "fields": ("categories", "years_experience", "timezone"),
            },
        ),
        (
            _("Contacts & Socials"),
            {
                "fields": ("phone", "instagram", "user"),
            },
        ),
        (
            _("Telegram Integration"),
            {
                "fields": ("telegram_id", "telegram_username", "bot_access_code", "qr_token"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        colors = {
            "active": "bg-green-500/20 text-green-700 dark:text-green-400",
            "vacation": "bg-yellow-500/20 text-yellow-700 dark:text-yellow-400",
            "training": "bg-blue-500/20 text-blue-700 dark:text-blue-400",
            "inactive": "bg-red-500/20 text-red-700 dark:text-red-400",
        }
        color_classes = colors.get(obj.status, "bg-gray-500/20 text-gray-700 dark:text-gray-400")
        return mark_safe(
            f'<span class="px-2 py-1 rounded-md text-xs font-medium {color_classes}">{obj.get_status_display()}</span>'
        )


@admin.register(Appointment)
class AppointmentAdmin(ModelAdmin):
    list_display = ("client", "master", "service", "datetime_start", "status_badge", "created_at")
    list_filter = ("status", "master", "created_at")
    search_fields = ("client__email", "master__name")
    date_hierarchy = "datetime_start"
    readonly_fields = ("datetime_start", "created_at", "updated_at")

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        colors = {
            "pending": "bg-yellow-500/20 text-yellow-700 dark:text-yellow-400",
            "confirmed": "bg-green-500/20 text-green-700 dark:text-green-400",
            "completed": "bg-blue-500/20 text-blue-700 dark:text-blue-400",
            "cancelled": "bg-red-500/20 text-red-700 dark:text-red-400",
        }
        color_classes = colors.get(obj.status, "bg-gray-500/20 text-gray-700 dark:text-gray-400")
        return mark_safe(
            f'<span class="px-2 py-1 rounded-md text-xs font-medium {color_classes}">{obj.get_status_display()}</span>'
        )


@admin.register(BookingSettings)
class BookingSettingsAdmin(ModelAdmin):
    list_display = ("__str__",)
    fieldsets = [
        (
            _("Resource Slot Grid"),
            {
                "fields": [
                    "step_minutes",
                    "default_buffer_between_minutes",
                    "min_advance_minutes",
                    "max_advance_days",
                ]
            },
        ),
        (_("Monday"), {"fields": ["monday_is_closed", "work_start_monday", "work_end_monday"]}),
        (_("Tuesday"), {"fields": ["tuesday_is_closed", "work_start_tuesday", "work_end_tuesday"]}),
        (_("Wednesday"), {"fields": ["wednesday_is_closed", "work_start_wednesday", "work_end_wednesday"]}),
        (_("Thursday"), {"fields": ["thursday_is_closed", "work_start_thursday", "work_end_thursday"]}),
        (_("Friday"), {"fields": ["friday_is_closed", "work_start_friday", "work_end_friday"]}),
        (_("Saturday"), {"fields": ["saturday_is_closed", "work_start_saturday", "work_end_saturday"]}),
        (_("Sunday"), {"fields": ["sunday_is_closed", "work_start_sunday", "work_end_sunday"]}),
        (
            _("Behavior"),
            {
                "fields": [
                    "load_strategy",
                    "book_only_from_next_day",
                ]
            },
        ),
    ]

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


class AppointmentGroupItemInline(TabularInline):
    model = AppointmentGroupItem
    extra = 0
    autocomplete_fields = ["appointment"]


@admin.register(AppointmentGroup)
class AppointmentGroupAdmin(ModelAdmin):
    list_display = ["id", "client", "status", "source", "combo", "created_at"]
    list_filter = ["status", "source", "combo"]
    search_fields = ["client__email", "client__first_name", "client__last_name", "group_token"]
    readonly_fields = ["group_token", "created_at", "updated_at"]
    inlines = [AppointmentGroupItemInline]

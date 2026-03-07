from django.contrib import admin
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from features.booking.models import (
    Appointment,
    AppointmentGroup,
    AppointmentGroupItem,
    BookingSettings,
    Master,
    MasterCertificate,
    MasterDayOff,
    MasterPortfolio,
)
from features.booking.models.client import Client
from unfold.admin import ModelAdmin, TabularInline


@admin.register(BookingSettings)
class BookingSettingsAdmin(ModelAdmin):
    list_display = ("__str__", "updated_at")

    fieldsets = (
        (
            _("General Settings"),
            {
                "fields": (
                    "default_step_minutes",
                    "default_buffer_between_minutes",
                    "default_min_advance_minutes",
                    "default_max_advance_days",
                )
            },
        ),
        (
            _("Notifications"),
            {
                "fields": (
                    "reminder_hours_before",
                    "admin_email_for_notifications",
                    "telegram_notification_channel_id",
                )
            },
        ),
        (
            _("Cancellation Policy"),
            {"fields": ("cancellation_window_hours",)},
        ),
    )

    def has_add_permission(self, request):
        # Singleton: only one instance allowed
        return not BookingSettings.objects.exists()


class MasterDayOffInline(TabularInline):
    model = MasterDayOff
    extra = 1
    classes = ["collapse"]


class MasterPortfolioInline(TabularInline):
    model = MasterPortfolio
    extra = 1
    classes = ["collapse"]


class MasterCertificateInline(TabularInline):
    model = MasterCertificate
    extra = 1
    classes = ["collapse"]


@admin.register(Master)
class MasterAdmin(ModelAdmin):
    list_display = ("name", "status_badge", "is_owner", "is_public", "order", "telegram_id")
    list_filter = ("status", "is_public", "is_owner", "categories")
    search_fields = ("name", "telegram_username", "phone")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MasterDayOffInline, MasterPortfolioInline, MasterCertificateInline]
    save_on_top = True

    fieldsets = (
        (
            _("Basic Info"),
            {"fields": ("name", "slug", "photo", "title", "short_description", "bio")},
        ),
        (
            _("Status & Visibility"),
            {"fields": ("status", "is_public", "is_owner", "is_featured", "order")},
        ),
        (
            _("Professional"),
            {"fields": ("categories", "years_experience")},
        ),
        (
            _("Schedule & Booking"),
            {
                "fields": (
                    "work_days",
                    "work_start",
                    "work_end",
                    "break_start",
                    "break_end",
                    "buffer_between_minutes",
                    "max_clients_parallel",
                ),
                "classes": ["collapse"],
            },
        ),
        (
            _("Contacts & Socials"),
            {"fields": ("phone", "instagram", "user")},
        ),
        (
            _("Telegram Integration"),
            {"fields": ("telegram_id", "telegram_username", "bot_access_code", "qr_token")},
        ),
    )

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        colors = {
            "active": "bg-green-500/20 text-green-700 dark:text-green-400",
            "vacation": "bg-yellow-500/20 text-yellow-700 dark:text-yellow-400",
            "fired": "bg-red-500/20 text-red-700 dark:text-red-400",
            "training": "bg-blue-500/20 text-blue-700 dark:text-blue-400",
        }
        # Admin-only status coloring
        # nosec B308,B703
        return mark_safe(
            f'<span class="px-2 py-1 rounded-md text-xs font-medium {colors.get(obj.status, "bg-gray-500/20")}">{obj.get_status_display()}</span>'
        )


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    list_display = ("full_name", "phone", "email", "telegram", "total_appointments", "status_badge")
    list_filter = ("status", "consent_marketing", "created_at")
    search_fields = ("first_name", "last_name", "phone", "email", "telegram")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            _("Personal Info"),
            {"fields": ("first_name", "last_name", "phone", "email", "photo")},
        ),
        (
            _("Socials"),
            {"fields": ("telegram", "instagram")},
        ),
        (
            _("Status"),
            {"fields": ("status", "notes", "consent_marketing")},
        ),
        (
            _("System"),
            {"fields": ("created_at", "updated_at", "user")},
        ),
    )

    @admin.display(description=_("Name"))
    def full_name(self, obj):
        return obj.display_name()

    @admin.display(description=_("Appointments"))
    def total_appointments(self, obj):
        return obj.appointments.count()

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        colors = {
            "guest": "bg-gray-500/20 text-gray-700 dark:text-gray-400",
            "active": "bg-green-500/20 text-green-700 dark:text-green-400",
            "blocked": "bg-red-500/20 text-red-700 dark:text-red-400",
        }
        return mark_safe(
            f'<span class="px-2 py-1 rounded-md text-xs font-medium {colors.get(obj.status, "bg-gray-500/20")}">{obj.get_status_display()}</span>'
        )


@admin.register(Appointment)
class AppointmentAdmin(ModelAdmin):
    list_display = (
        "id",
        "client_link",
        "master_link",
        "service_link",
        "datetime_start",
        "status_badge",
        "price",
        "source",
    )
    list_filter = ("status", "source", "master", "datetime_start", "created_at")
    search_fields = ("client__first_name", "client__last_name", "client__phone", "id")
    date_hierarchy = "datetime_start"
    readonly_fields = ("created_at", "updated_at", "finalize_token")

    fieldsets = (
        (
            _("Main Info"),
            {"fields": ("client", "master", "service", "datetime_start", "duration_minutes")},
        ),
        (
            _("Status & Payment"),
            {"fields": ("status", "price", "price_actual", "source", "active_promo")},
        ),
        (
            _("Cancellation"),
            {"fields": ("cancelled_at", "cancel_reason", "cancel_note"), "classes": ["collapse"]},
        ),
        (
            _("Notes"),
            {"fields": ("client_notes", "admin_notes")},
        ),
        (
            _("System"),
            {"fields": ("created_at", "updated_at", "finalize_token", "reminder_sent", "reminder_sent_at")},
        ),
    )

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        colors = {
            "pending": "bg-yellow-500/20 text-yellow-700 dark:text-yellow-400",
            "confirmed": "bg-green-500/20 text-green-700 dark:text-green-400",
            "completed": "bg-blue-500/20 text-blue-700 dark:text-blue-400",
            "cancelled": "bg-red-500/20 text-red-700 dark:text-red-400",
            "no_show": "bg-gray-500/20 text-gray-700 dark:text-gray-400",
            "reschedule_proposed": "bg-purple-500/20 text-purple-700 dark:text-purple-400",
        }
        # Admin-only status coloring
        # nosec B308,B703
        return mark_safe(
            f'<span class="px-2 py-1 rounded-md text-xs font-medium {colors.get(obj.status, "bg-gray-500/20")}">{obj.get_status_display()}</span>'
        )

    @admin.display(description=_("Client"))
    def client_link(self, obj):
        return obj.client

    @admin.display(description=_("Master"))
    def master_link(self, obj):
        return obj.master

    @admin.display(description=_("Service"))
    def service_link(self, obj):
        return obj.service


class AppointmentGroupItemInline(TabularInline):
    model = AppointmentGroupItem
    extra = 0
    readonly_fields = ("appointment", "service", "order")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AppointmentGroup)
class AppointmentGroupAdmin(ModelAdmin):
    list_display = ("id", "client", "booking_date", "status_badge", "total_duration_minutes", "created_at")
    list_filter = ("status", "booking_date", "engine_mode")
    search_fields = ("client__first_name", "client__phone", "id")
    inlines = [AppointmentGroupItemInline]
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        colors = {
            "pending": "bg-yellow-500/20 text-yellow-700 dark:text-yellow-400",
            "confirmed": "bg-green-500/20 text-green-700 dark:text-green-400",
            "completed": "bg-blue-500/20 text-blue-700 dark:text-blue-400",
            "cancelled": "bg-red-500/20 text-red-700 dark:text-red-400",
            "partial": "bg-orange-500/20 text-orange-700 dark:text-orange-400",
        }
        color_classes = mark_safe(colors.get(obj.status, "bg-gray-500/20 text-gray-700 dark:text-gray-400"))  # nosec
        return mark_safe(
            f'<span class="px-2 py-1 rounded-md text-xs font-medium {color_classes}">{obj.get_status_display()}</span>'
        )

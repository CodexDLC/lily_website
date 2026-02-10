"""Admin interface for booking app."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Appointment, Client, Master, MasterCertificate, MasterPortfolio


@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    """Admin interface for Master model."""

    list_display = ["name", "status_badge", "is_owner", "is_featured", "years_experience", "order"]
    list_filter = ["status", "is_owner", "is_featured", "categories"]
    search_fields = ["name", "slug", "phone", "instagram", "telegram_username"]
    readonly_fields = ["bot_access_code", "qr_token", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("name", "slug", "photo", "title", "bio", "short_description")},
        ),
        (
            _("Specializations"),
            {"fields": ("service_groups", "categories", "years_experience")},
        ),
        (
            _("Contact"),
            {"fields": ("phone", "instagram")},
        ),
        (
            _("Status & Flags"),
            {"fields": ("status", "is_owner", "is_featured", "order")},
        ),
        (
            _("Django User"),
            {"fields": ("user",), "classes": ("collapse",)},
        ),
        (
            _("Telegram Integration"),
            {
                "fields": ("telegram_id", "telegram_username", "bot_access_code"),
                "classes": ("collapse",),
            },
        ),
        (
            _("QR System (Future)"),
            {"fields": ("qr_token",), "classes": ("collapse",)},
        ),
        (
            _("SEO"),
            {"fields": ("seo_title", "seo_description", "seo_image"), "classes": ("collapse",)},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    filter_horizontal = ["service_groups", "categories"]

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        """Colored status badge."""
        colors = {
            "active": "green",
            "vacation": "orange",
            "fired": "red",
            "training": "blue",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="padding:3px 10px;background:{};color:white;border-radius:3px;">{}</span>',
            color,
            obj.get_status_display(),
        )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin interface for Client model."""

    list_display = ["display_name_admin", "phone", "email", "status_badge", "is_ghost_icon", "created_at"]
    list_filter = ["status", "consent_marketing", "created_at"]
    search_fields = ["name", "phone", "email", "access_token"]
    readonly_fields = ["access_token", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Contact Information"),
            {"fields": ("name", "phone", "email")},
        ),
        (
            _("Account Status"),
            {"fields": ("status", "user", "access_token")},
        ),
        (
            _("Marketing"),
            {"fields": ("consent_marketing", "consent_date")},
        ),
        (
            _("Internal"),
            {"fields": ("notes", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    @admin.display(description=_("Name"))
    def display_name_admin(self, obj):
        """Name with ghost indicator."""
        return obj.display_name()

    @admin.display(description=_("Ghost"), boolean=True)
    def is_ghost_icon(self, obj):
        """Ghost account indicator."""
        return obj.is_ghost

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        """Colored status badge."""
        colors = {
            "guest": "orange",
            "active": "green",
            "blocked": "red",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="padding:3px 10px;background:{};color:white;border-radius:3px;">{}</span>',
            color,
            obj.get_status_display(),
        )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin interface for Appointment model."""

    list_display = [
        "id",
        "client_name_display",
        "master",
        "service",
        "datetime_start",
        "duration_minutes",
        "status_badge",
        "price",
    ]
    list_filter = ["status", "master", "datetime_start", "created_at"]
    search_fields = [
        "client__name",
        "client__phone",
        "client__email",
        "master__name",
        "service__title",
    ]
    readonly_fields = ["created_at", "updated_at", "cancelled_at", "reminder_sent_at"]
    date_hierarchy = "datetime_start"

    fieldsets = (
        (
            _("Booking Details"),
            {"fields": ("client", "master", "service", "datetime_start", "duration_minutes", "price")},
        ),
        (
            _("Status"),
            {"fields": ("status", "cancelled_at", "cancel_reason", "cancel_note")},
        ),
        (
            _("Notes"),
            {"fields": ("client_notes", "admin_notes")},
        ),
        (
            _("Notifications"),
            {"fields": ("reminder_sent", "reminder_sent_at"), "classes": ("collapse",)},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = ["mark_as_confirmed", "mark_as_completed", "cancel_appointments"]

    @admin.display(description=_("Client"))
    def client_name_display(self, obj):
        """Client name for list display."""
        return obj.client.display_name()

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        """Colored status badge."""
        colors = {
            "pending": "orange",
            "confirmed": "green",
            "completed": "blue",
            "cancelled": "red",
            "no_show": "gray",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="padding:3px 10px;background:{};color:white;border-radius:3px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description=_("Mark as Confirmed"))
    def mark_as_confirmed(self, request, queryset):
        """Mark selected appointments as confirmed."""
        queryset.update(status=Appointment.STATUS_CONFIRMED)

    @admin.action(description=_("Mark as Completed"))
    def mark_as_completed(self, request, queryset):
        """Mark selected appointments as completed."""
        queryset.filter(status=Appointment.STATUS_CONFIRMED).update(status=Appointment.STATUS_COMPLETED)

    @admin.action(description=_("Cancel Selected"))
    def cancel_appointments(self, request, queryset):
        """Cancel selected appointments."""
        queryset.update(status=Appointment.STATUS_CANCELLED, cancel_reason=Appointment.CANCEL_REASON_OTHER)


@admin.register(MasterCertificate)
class MasterCertificateAdmin(admin.ModelAdmin):
    """Admin interface for MasterCertificate model."""

    list_display = ["title", "master", "issuer", "issue_date", "order", "is_active"]
    list_filter = ["master", "is_active", "issue_date"]
    search_fields = ["title", "issuer", "master__name"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            _("Certificate Info"),
            {"fields": ("master", "title", "issuer", "issue_date", "image")},
        ),
        (
            _("Display"),
            {"fields": ("order", "is_active")},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(MasterPortfolio)
class MasterPortfolioAdmin(admin.ModelAdmin):
    """Admin interface for MasterPortfolio model."""

    list_display = ["master", "service", "order", "is_active", "created_at"]
    list_filter = ["master", "service", "is_active", "created_at"]
    search_fields = ["master__name", "service__title", "description"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            _("Portfolio Item"),
            {"fields": ("master", "image", "description", "service")},
        ),
        (
            _("Display"),
            {"fields": ("order", "is_active")},
        ),
        (
            _("Instagram"),
            {"fields": ("instagram_url",), "classes": ("collapse",)},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

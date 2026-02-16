"""Admin interface for booking app using Unfold."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin
from unfold.decorators import action

from .models import Appointment, Client, Master, MasterCertificate, MasterPortfolio


@admin.register(Master)
class MasterAdmin(ModelAdmin, TranslationAdmin):
    list_display = ["name", "status_badge", "is_owner", "order"]
    list_display_links = ["name"]
    list_filter = ["status", "is_owner"]
    search_fields = ["name"]

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        colors = {
            "active": "bg-green-500/20 text-green-700 dark:text-green-400",
            "vacation": "bg-orange-500/20 text-orange-700 dark:text-orange-400",
        }
        color_classes = mark_safe(colors.get(obj.status, "bg-gray-500/20 text-gray-700 dark:text-gray-400"))
        return format_html(
            '<span class="px-2 py-1 rounded-md text-xs font-medium {}">{}</span>',
            color_classes,
            obj.get_status_display(),
        )


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    list_display = ["first_name", "last_name", "phone", "email", "created_at"]
    list_display_links = ["first_name", "last_name"]


@admin.register(Appointment)
class AppointmentAdmin(ModelAdmin):
    list_display = ["id", "client", "master", "service", "datetime_start", "status_badge"]
    list_display_links = ["id", "client"]
    list_filter = ["status", "master"]
    list_filter_sheet = True

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        colors = {
            "pending": "bg-amber-500/20 text-amber-700 dark:text-amber-400",
            "confirmed": "bg-green-500/20 text-green-700 dark:text-green-400",
            "completed": "bg-blue-500/20 text-blue-700 dark:text-blue-400",
            "cancelled": "bg-red-500/20 text-red-700 dark:text-red-400",
        }
        color_classes = mark_safe(colors.get(obj.status, "bg-gray-500/20 text-gray-700 dark:text-gray-400"))
        return format_html(
            '<span class="px-2 py-1 rounded-md text-xs font-medium {}">{}</span>',
            color_classes,
            obj.get_status_display(),
        )

    @action(description=_("Mark as Confirmed"), icon="check_circle")
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status=Appointment.STATUS_CONFIRMED)


@admin.register(MasterCertificate)
class MasterCertificateAdmin(ModelAdmin, TranslationAdmin):
    list_display = ["title", "master", "is_active"]


@admin.register(MasterPortfolio)
class MasterPortfolioAdmin(ModelAdmin, TranslationAdmin):
    list_display = ["master", "service", "is_active"]

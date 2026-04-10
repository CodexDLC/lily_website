from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from ..models.client import Client


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    list_display = ("id", "full_name", "phone", "email", "status", "is_ghost", "created_at")
    list_display_links = ("id", "full_name")
    list_filter = ("status", "is_ghost", "consent_marketing")
    search_fields = ("first_name", "last_name", "phone", "email")
    readonly_fields = ("access_token", "created_at", "updated_at")
    fieldsets = (
        (_("User Link"), {"fields": ("user",)}),
        (_("Personal Info"), {"fields": ("first_name", "last_name", "patronymic")}),
        (_("Contact"), {"fields": ("email", "phone")}),
        (_("Consents"), {"fields": ("consent_marketing", "consent_analytics", "consent_date")}),
        (_("Status"), {"fields": ("status", "is_ghost", "access_token", "note")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

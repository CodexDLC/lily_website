from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import NotificationRecipient


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(ModelAdmin):
    list_display = ("email", "name", "kind", "enabled")
    list_filter = ("kind", "enabled")
    search_fields = ("email", "name", "note")
    ordering = ("email",)

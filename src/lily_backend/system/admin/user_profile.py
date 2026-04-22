from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from ..models.user_profile import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ("id", "user", "get_full_name", "phone", "source", "created_at")
    list_display_links = ("id", "user")
    list_filter = ("source", "notify_service", "notify_reminders")
    search_fields = ("user__username", "user__email", "first_name", "last_name", "phone")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (_("User"), {"fields": ("user",)}),
        (_("Personal Data"), {"fields": ("first_name", "last_name", "patronymic", "birth_date", "phone", "avatar")}),
        (_("Social Media"), {"fields": ("instagram", "telegram")}),
        (_("Source & Notes"), {"fields": ("source", "notes")}),
        (_("Privacy"), {"fields": ("show_avatar", "show_birth_date", "show_visit_history", "use_recommendations")}),
        (_("Notifications"), {"fields": ("notify_service", "notify_reminders")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

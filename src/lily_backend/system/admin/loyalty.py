from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from ..models.loyalty import LoyaltyProfile


@admin.register(LoyaltyProfile)
class LoyaltyProfileAdmin(ModelAdmin):
    list_display = (
        "id",
        "profile",
        "level",
        "best_level",
        "progress_percent",
        "behavior_multiplier",
        "calculated_at",
    )
    list_display_links = ("id", "profile")
    list_filter = ("level", "best_level")
    search_fields = ("profile__user__username", "profile__user__email", "profile__first_name", "profile__last_name")
    readonly_fields = (
        "profile",
        "level",
        "best_level",
        "progress_percent",
        "effective_spend_score",
        "behavior_multiplier",
        "source_hash",
        "calculated_at",
        "stats",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (_("Profile"), {"fields": ("profile",)}),
        (_("Loyalty Snapshot"), {"fields": ("level", "best_level", "progress_percent")}),
        (
            _("Internal Calculation"),
            {"fields": ("effective_spend_score", "behavior_multiplier", "source_hash", "stats")},
        ),
        (_("Timestamps"), {"fields": ("calculated_at", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

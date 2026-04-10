from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin

from ..models import Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(TranslationAdmin, ModelAdmin):
    list_display = ["name", "slug", "bento_group", "is_active", "is_planned", "order"]
    list_display_links = ["name"]
    list_editable = ["order", "bento_group", "is_active", "is_planned"]
    search_fields = ("name",)
    prepopulated_fields = {"slug": ["name"]}

    fieldsets = (
        (
            _("Basic Info"),
            {
                "fields": (
                    "is_active",
                    "is_planned",
                ),
            },
        ),
        (
            _("Content"),
            {
                "fields": ("description", "content"),
            },
        ),
        (
            _("System"),
            {
                "fields": ("order",),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Service)
class ServiceAdmin(TranslationAdmin, ModelAdmin):
    list_display = ["name", "category", "price", "duration", "order", "is_active", "is_addon"]
    list_display_links = ["name"]
    list_editable = ["price", "duration", "order", "is_active", "is_addon"]
    list_filter = ("category", "is_active", "is_addon")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ["name"]}

    fieldsets = (
        (
            _("Basic Info"),
            {
                "fields": (
                    "name",
                    "slug",
                    "category",
                    "image",
                    "is_active",
                    "is_hit",
                    "is_addon",
                ),
            },
        ),
        (
            _("Pricing & Duration"),
            {
                "fields": (
                    ("price", "price_info"),
                    ("duration", "duration_info"),
                ),
            },
        ),
        (
            _("Content"),
            {
                "fields": ("description", "content"),
            },
        ),
        (
            _("System"),
            {
                "fields": ("order", "masters", "excludes"),
                "classes": ("collapse",),
            },
        ),
    )

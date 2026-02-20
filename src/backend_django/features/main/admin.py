"""Admin interface for main app using Unfold."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin

from .models import Category, ContactRequest, PortfolioImage, Service


@admin.register(Category)
class CategoryAdmin(ModelAdmin, TranslationAdmin):
    list_display = ["title", "slug", "is_active", "order"]
    list_display_links = ["title"]
    list_editable = ["order"]
    search_fields = ["title"]
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (
            _("Basic Info"),
            {
                "fields": ("title", "slug", "image", "bento_group", "is_active", "is_planned"),
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
        (
            _("SEO"),
            {
                "fields": ("seo_title", "seo_description", "seo_image"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Service)
class ServiceAdmin(ModelAdmin, TranslationAdmin):
    list_display = ["title", "category", "price", "duration", "order", "is_active"]
    list_display_links = ["title"]
    list_editable = ["price", "duration", "order"]
    list_filter = ["category", "is_active"]
    ordering = ["order", "title"]
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (
            _("Basic Info"),
            {
                "fields": ("title", "slug", "category", "image", "is_active", "is_hit"),
            },
        ),
        (
            _("Pricing & Duration"),
            {
                "fields": (("price", "price_info"), ("duration", "duration_info")),
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
        (
            _("SEO"),
            {
                "fields": ("seo_title", "seo_description", "seo_image"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(PortfolioImage)
class PortfolioImageAdmin(ModelAdmin):
    list_display = ["title", "service", "order"]
    list_editable = ["order"]


@admin.register(ContactRequest)
class ContactRequestAdmin(ModelAdmin):
    list_display = ["client", "topic", "is_processed", "created_at"]
    list_filter = ["topic", "is_processed"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["client__first_name", "client__last_name", "message"]

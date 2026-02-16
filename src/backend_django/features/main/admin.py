"""Admin interface for main app using Unfold."""

from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin

from .models import Category, PortfolioImage, Service


@admin.register(Category)
class CategoryAdmin(ModelAdmin, TranslationAdmin):
    list_display = ["title", "slug", "is_active", "order"]
    list_display_links = ["title"]
    search_fields = ["title"]


@admin.register(Service)
class ServiceAdmin(ModelAdmin, TranslationAdmin):
    list_display = ["title", "category", "price", "is_active"]
    list_display_links = ["title"]
    list_filter = ["category", "is_active"]


@admin.register(PortfolioImage)
class PortfolioImageAdmin(ModelAdmin):
    list_display = ["title", "service", "order"]

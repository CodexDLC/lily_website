"""Admin interface for main app."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from .models import Category, PortfolioImage, Service

# ══════════════════════════════════════════════════════════════════════════════
# INLINES
# ══════════════════════════════════════════════════════════════════════════════


class PortfolioImageInline(admin.TabularInline):
    """Inline for portfolio images inside Service."""

    model = PortfolioImage
    extra = 1
    fields = ["image", "title", "order"]
    ordering = ["order"]


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN CLASSES
# ══════════════════════════════════════════════════════════════════════════════


@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    """Admin interface for Category model."""

    list_display = ["title", "slug", "bento_group", "order", "active_badge", "planned_badge", "service_count"]
    list_filter = ["bento_group", "is_active", "is_planned"]
    search_fields = ["title", "slug", "description"]
    prepopulated_fields = {"slug": ("title",)}
    ordering = ["order", "title"]

    fieldsets = [
        (
            _("Status & Display"),
            {"fields": ("is_active", "is_planned", "order", "bento_group")},
        ),
        (
            _("Content"),
            {"fields": ("title", "slug", "description", "content", "image", "icon")},
        ),
        (
            _("SEO"),
            {"fields": ("seo_title", "seo_description", "seo_image"), "classes": ("collapse",)},
        ),
    ]

    @admin.display(description=_("Status"))
    def active_badge(self, obj):
        """Active status badge."""
        if obj.is_active:
            return format_html(
                '<span style="padding:3px 10px;background:green;color:white;border-radius:3px;">✓ {}</span>',
                _("Active"),
            )
        return format_html(
            '<span style="padding:3px 10px;background:gray;color:white;border-radius:3px;">✗ {}</span>',
            _("Hidden"),
        )

    @admin.display(description=_("Planned"))
    def planned_badge(self, obj):
        """Planned/Coming Soon badge."""
        if obj.is_planned:
            return format_html(
                '<span style="padding:3px 10px;background:blue;color:white;border-radius:3px;">🚀 {}</span>',
                _("Coming Soon"),
            )
        return "—"

    @admin.display(description=_("Services"))
    def service_count(self, obj):
        """Count of services in this category."""
        count = Service.objects.filter(category=obj).count()
        return format_html("<strong>{}</strong> {}", count, _("services"))


@admin.register(Service)
class ServiceAdmin(TranslationAdmin):
    """Admin interface for Service model."""

    list_display = [
        "title",
        "category",
        "price_display",
        "duration",
        "order",
        "active_badge",
        "hit_badge",
        "planned_badge",
    ]
    list_filter = ["category", "is_active", "is_hit", "is_planned", "is_available"]
    search_fields = ["title", "description"]
    prepopulated_fields = {"slug": ("title",)}
    ordering = ["category", "order"]
    inlines = [PortfolioImageInline]

    fieldsets = [
        (
            _("Status & Flags"),
            {"fields": ("is_active", "is_available", "is_planned", "is_hit", "order")},
        ),
        (
            _("Relation"),
            {"fields": ("category",)},
        ),
        (
            _("Service Info"),
            {"fields": ("title", "slug", "price", "price_info", "duration")},
        ),
        (
            _("Description"),
            {"fields": ("description", "content", "image")},
        ),
        (
            _("SEO"),
            {"fields": ("seo_title", "seo_description", "seo_image"), "classes": ("collapse",)},
        ),
    ]

    actions = ["mark_as_hit", "remove_hit", "mark_as_available", "mark_as_unavailable"]

    @admin.display(description=_("Price"))
    def price_display(self, obj):
        """Price with currency."""
        return format_html('<strong style="color:green;">{} €</strong>', obj.price)

    @admin.display(description=_("Status"))
    def active_badge(self, obj):
        """Active status badge."""
        if not obj.is_active:
            return format_html(
                '<span style="padding:3px 10px;background:gray;color:white;border-radius:3px;">✗ {}</span>',
                _("Hidden"),
            )
        if not obj.is_available:
            return format_html(
                '<span style="padding:3px 10px;background:orange;color:white;border-radius:3px;">⚠ {}</span>',
                _("Unavailable"),
            )
        return format_html(
            '<span style="padding:3px 10px;background:green;color:white;border-radius:3px;">✓ {}</span>',
            _("Active"),
        )

    @admin.display(description=_("Hit"))
    def hit_badge(self, obj):
        """Hit/Popular badge."""
        if obj.is_hit:
            return format_html(
                '<span style="padding:3px 10px;background:red;color:white;border-radius:3px;">🔥 {}</span>',
                _("HIT"),
            )
        return "—"

    @admin.display(description=_("Planned"))
    def planned_badge(self, obj):
        """Planned/Coming Soon badge."""
        if obj.is_planned:
            return format_html(
                '<span style="padding:3px 10px;background:blue;color:white;border-radius:3px;">🚀 {}</span>',
                _("Soon"),
            )
        return "—"

    @admin.action(description=_("✓ Mark as HIT"))
    def mark_as_hit(self, request, queryset):
        """Mark selected services as hit."""
        queryset.update(is_hit=True)

    @admin.action(description=_("✗ Remove HIT"))
    def remove_hit(self, request, queryset):
        """Remove hit status from selected services."""
        queryset.update(is_hit=False)

    @admin.action(description=_("✓ Mark as Available"))
    def mark_as_available(self, request, queryset):
        """Mark selected services as available."""
        queryset.update(is_available=True)

    @admin.action(description=_("⚠ Mark as Unavailable"))
    def mark_as_unavailable(self, request, queryset):
        """Mark selected services as unavailable."""
        queryset.update(is_available=False)


@admin.register(PortfolioImage)
class PortfolioImageAdmin(admin.ModelAdmin):
    """Admin interface for PortfolioImage model."""

    list_display = ["title", "service", "order", "image_preview"]
    list_filter = ["service__category"]
    search_fields = ["title", "service__title"]
    ordering = ["service", "order"]

    fieldsets = [
        (
            _("Image"),
            {"fields": ("service", "image", "title", "order")},
        ),
    ]

    @admin.display(description=_("Preview"))
    def image_preview(self, obj):
        """Show small image preview."""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:cover;border-radius:3px;" />',
                obj.image.url,
            )
        return "—"

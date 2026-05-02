from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from ..models import ServiceCombo, ServiceComboItem, ServiceConflictRule


class ServiceComboItemInline(TabularInline):
    model = ServiceComboItem
    extra = 1
    fields = ["service", "is_required", "order"]
    autocomplete_fields = ["service"]


@admin.register(ServiceCombo)
class ServiceComboAdmin(ModelAdmin):
    list_display = [
        "name",
        "slug",
        "discount_type",
        "discount_value",
        "is_featured",
        "show_on_home",
        "is_active",
        "valid_from",
        "valid_until",
    ]
    list_display_links = ["name"]
    list_editable = ["discount_value", "is_featured", "show_on_home", "is_active"]
    list_filter = ["discount_type", "is_featured", "show_on_home", "is_active"]
    search_fields = ["name", "slug"]
    warning_fields = ["discount_value"]
    prepopulated_fields = {"slug": ["name"]}
    inlines = [ServiceComboItemInline]

    fieldsets = (
        (
            _("Basic Info"),
            {"fields": ("name", "slug", "description", "is_active")},
        ),
        (
            _("Promo display"),
            {
                "fields": (
                    "is_featured",
                    "show_on_home",
                    "promo_order",
                    "promo_title",
                    "promo_text",
                    "promo_image",
                    "promo_button_text",
                )
            },
        ),
        (
            _("Discount"),
            {"fields": ("discount_type", "discount_value")},
        ),
        (
            _("Promo period"),
            {"fields": ("valid_from", "valid_until"), "classes": ("collapse",)},
        ),
    )


@admin.register(ServiceConflictRule)
class ServiceConflictRuleAdmin(ModelAdmin):
    list_display = ["source", "rule_type", "target", "is_active", "note"]
    list_display_links = ["source"]
    list_filter = ["rule_type", "is_active"]
    search_fields = ["source__name", "target__name", "note"]
    list_editable = ["is_active"]
    autocomplete_fields = ["source", "target"]

    actions = ["make_reverse_rules"]

    @admin.action(description=_("Add reverse replaces rule for selected"))
    def make_reverse_rules(self, request, queryset):
        created = 0
        for rule in queryset.filter(rule_type=ServiceConflictRule.REPLACES):
            _, was_created = ServiceConflictRule.objects.get_or_create(
                source=rule.target,
                target=rule.source,
                rule_type=ServiceConflictRule.REPLACES,
                defaults={"note": f"Auto-reverse of rule #{rule.pk}"},
            )
            if was_created:
                created += 1
        self.message_user(request, f"Created {created} reverse rule(s).")

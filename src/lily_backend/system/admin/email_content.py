from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin

from ..models import EmailContent


@admin.register(EmailContent)
class EmailContentAdmin(TabbedTranslationAdmin):
    list_display = ["key", "category", "description"]
    list_filter = ("category",)
    search_fields = ("key", "text", "description")
    ordering = ("category", "key")
    fieldsets = (
        (None, {"fields": ("key", "category", "description")}),
        (_("Text Content"), {"fields": ("text_de", "text_ru", "text_uk", "text_en")}),
    )

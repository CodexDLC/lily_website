from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import PageView


@admin.register(PageView)
class PageViewAdmin(ModelAdmin):
    list_display = ("date", "path", "views")
    list_filter = ("date",)
    search_fields = ("path",)
    readonly_fields = ("date", "path", "views")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

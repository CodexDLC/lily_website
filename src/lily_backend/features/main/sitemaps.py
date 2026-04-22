from codex_django.core.sitemaps import BaseSitemap
from django.urls import reverse
from features.main.models import ServiceCategory


class CategorySitemap(BaseSitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return ServiceCategory.objects.all()

    def lastmod(self, obj):
        actual_obj = obj[0] if isinstance(obj, list | tuple) else obj
        return getattr(actual_obj, "updated_at", None)

    def location(self, obj):
        actual_obj = obj[0] if isinstance(obj, list | tuple) else obj
        return reverse("main:service_detail", kwargs={"slug": actual_obj.slug})

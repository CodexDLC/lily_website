# Import BaseSitemap from core to ensure canonical domain
from core.sitemaps import BaseSitemap
from django.urls import reverse
from features.main.models import Category


class CategorySitemap(BaseSitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)

    def lastmod(self, obj):
        # obj might be a tuple (Category, lang_code) if i18n=True is in BaseSitemap
        actual_obj = obj[0] if isinstance(obj, list | tuple) else obj
        return actual_obj.updated_at

    def location(self, obj):
        # Handle cases where Django passes (item, lang_code) tuple
        actual_obj = obj[0] if isinstance(obj, list | tuple) else obj
        return reverse("service_detail", kwargs={"slug": actual_obj.slug})

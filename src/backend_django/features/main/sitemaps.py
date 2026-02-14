from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from features.main.models import Category


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("service_detail", kwargs={"slug": obj.slug})

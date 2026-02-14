from django.contrib.sitemaps import Sitemap
from django.urls import reverse

# Import CategorySitemap from features.main
from features.main.sitemaps import CategorySitemap


class StaticSitemap(Sitemap):
    priority = 0.8
    changefreq = "monthly"

    def items(self):
        return ["home", "services", "team", "contacts", "impressum", "datenschutz"]

    def location(self, item):
        return reverse(item)


# Define the sitemaps dictionary, including CategorySitemap
sitemaps = {
    "static": StaticSitemap,
    "categories": CategorySitemap,  # Add Sitemap for categories
}

# If you have models for which you need to generate a sitemap,
# for example, for each service or article, you can add them like this:
# from .models import Service

# class ServiceSitemap(Sitemap):
#     changefreq = "weekly"
#     priority = 0.6

#     def items(self):
#         return Service.objects.all()

#     def lastmod(self, obj):
#         return obj.updated_at # Assumes your Service model has an updated_at field

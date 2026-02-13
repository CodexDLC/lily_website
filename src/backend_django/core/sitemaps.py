from django.contrib.sitemaps import Sitemap
from django.urls import reverse

# Импортируем CategorySitemap из features.main
from features.main.sitemaps import CategorySitemap


class StaticSitemap(Sitemap):
    priority = 0.8
    changefreq = "monthly"

    def items(self):
        return ["home", "services", "team", "contacts", "impressum", "datenschutz"]

    def location(self, item):
        return reverse(item)


# Определяем словарь sitemaps, включая CategorySitemap
sitemaps = {
    "static": StaticSitemap,
    "categories": CategorySitemap,  # Добавляем Sitemap для категорий
}

# Если у вас есть модели, для которых нужно генерировать sitemap,
# например, для каждой услуги или статьи, вы можете добавить их так:
# from .models import Service

# class ServiceSitemap(Sitemap):
#     changefreq = "weekly"
#     priority = 0.6

#     def items(self):
#         return Service.objects.all()

#     def lastmod(self, obj):
#         return obj.updated_at # Предполагается, что у вашей модели Service есть поле updated_at

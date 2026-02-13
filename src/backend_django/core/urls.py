"""
lily_website — URL Configuration.

Features auto-included via include().
"""

from api.urls import api
from core.sitemaps import StaticSitemap  # Убедитесь, что core/sitemaps.py существует
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

# Импортируем sitemap и наши классы sitemap
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView
from features.main.sitemaps import CategorySitemap  # Импортируем CategorySitemap

# Определяем словарь sitemaps
sitemaps = {
    "static": StaticSitemap,
    "categories": CategorySitemap,  # Добавляем Sitemap для категорий
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    # SEO & AI Files
    path("llms.txt", TemplateView.as_view(template_name="llms.txt", content_type="text/plain")),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    # Sitemap
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    # Features
    path("", include("features.booking.urls")),  # Booking Wizard
    path("", include("features.main.urls")),  # Main Site
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers (must be at the top level of urls.py)
# These will only be used when DEBUG = False
handler400 = "django.views.defaults.bad_request"
handler403 = "django.views.defaults.permission_denied"
handler404 = "django.views.defaults.page_not_found"
handler500 = "django.views.defaults.server_error"

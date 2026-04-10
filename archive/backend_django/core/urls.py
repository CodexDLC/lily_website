"""
lily_website — URL Configuration.

Features auto-included via include().
"""

from api.urls import api
from core.sitemaps import sitemaps
from core.views import LLMSTextView
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.static import serve

# Non-i18n patterns (technical URLs, API, etc.)
urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),  # For set_language view
    path("api/", api.urls),
    path("", include("django_prometheus.urls")),  # Prometheus metrics
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    # PWA files
    path("manifest.json", serve, {"path": "manifest.json", "document_root": settings.STATICFILES_DIRS[0]}),
    path("sw.js", serve, {"path": "sw.js", "document_root": settings.STATICFILES_DIRS[0]}),
]

# i18n patterns (URLs with language prefix)
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("cabinet/", include("features.cabinet.urls", namespace="cabinet")),
    # SEO & AI Files
    path("llms.txt", LLMSTextView.as_view()),
    # Features
    path("", include("features.booking.urls", namespace="booking")),
    path("", include("features.main.urls")),
)

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler400 = "django.views.defaults.bad_request"
handler403 = "django.views.defaults.permission_denied"
handler404 = "django.views.defaults.page_not_found"
handler500 = "django.views.defaults.server_error"

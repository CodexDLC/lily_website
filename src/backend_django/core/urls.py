"""
lily_website — URL Configuration.

Features auto-included via include().
"""

from api.urls import api
from core.sitemaps import sitemaps  # Импортируем словарь sitemaps напрямую
from core.views import LLMSTextView
from django.conf import settings

# Импортируем i18n_patterns и LLMSTextView
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin

# Импортируем sitemap и наши классы sitemap
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

# Non-i18n patterns (technical URLs, API, etc.)
urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),  # For set_language view
    path("api/", api.urls),
    path("", include("django_prometheus.urls")),  # Prometheus metrics
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
]

# i18n patterns (URLs with language prefix)
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    # SEO & AI Files (localized versions if needed, or handled by view logic)
    path("llms.txt", LLMSTextView.as_view()),
    # Features
    path("", include("features.booking.urls")),  # Booking Wizard
    path("", include("features.main.urls")),  # Main Site
)

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

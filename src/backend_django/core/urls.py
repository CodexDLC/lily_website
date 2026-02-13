"""
lily_website — URL Configuration.

Features auto-included via include().
"""

from api.urls import api
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    # SEO & AI Files
    path("llms.txt", TemplateView.as_view(template_name="llms.txt", content_type="text/plain")),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    # Features
    path("", include("features.booking.urls")),  # Booking Wizard
    path("", include("features.main.urls")),  # Main Site
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

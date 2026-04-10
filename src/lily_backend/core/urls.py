from typing import Any

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView
from system.api import api
from unfold.sites import UnfoldAdminSite

from core.sitemaps import sitemaps

# Inject UnfoldAdminSite into default admin
admin.site.__class__ = UnfoldAdminSite

# Error Handlers
handler404 = "system.views.errors.handler404"
handler500 = "system.views.errors.handler500"
handler403 = "system.views.errors.handler403"
handler400 = "system.views.errors.handler400"

# Patterns
urlpatterns: list[Any] = [
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("i18n/", include("django.conf.urls.i18n")),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("llms_de.txt", TemplateView.as_view(template_name="llms_de.txt", content_type="text/plain")),
    path("llms_en.txt", TemplateView.as_view(template_name="llms_en.txt", content_type="text/plain")),
    path("api/", api.urls),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("cabinet/", include("cabinet.urls")),
    path("system/", include("system.urls")),
    path("showcase/", include("codex_django.showcase.urls")),
    path("conversations/", include("features.conversations.urls")),
    path("", include("features.booking.urls")),
    path("", include("features.main.urls", namespace="main")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

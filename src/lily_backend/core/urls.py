from typing import Any

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView
from features.booking.api.bot import router as bot_router
from features.conversations.api import router as conversations_router
from features.conversations.views.unsubscribe import UnsubscribeView
from system.api import api
from system.api.tracking import router as tracking_router
from unfold.sites import UnfoldAdminSite

from core.sitemaps import sitemaps
from core.views import LLMSTextView

# Register Ninja routers here to avoid circular imports during startup
api.add_router("/v1/booking", bot_router)
api.add_router("/v1/conversations", conversations_router)
api.add_router("/v1/tracking", tracking_router)

# Inject UnfoldAdminSite into default admin
admin.site.__class__ = UnfoldAdminSite

# Error Handlers
handler404 = "system.views.errors.handler404"
handler500 = "system.views.errors.handler500"
handler403 = "system.views.errors.handler403"
handler400 = "system.views.errors.handler400"
handler405 = "system.views.errors.handler405"

# Patterns
urlpatterns: list[Any] = [
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("i18n/", include("django.conf.urls.i18n")),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path(
        "sw.js",
        TemplateView.as_view(template_name="sw.js", content_type="application/javascript"),
        name="sw_js",
    ),
    path(
        "manifest.json",
        TemplateView.as_view(template_name="manifest.json", content_type="application/json"),
        name="manifest_json",
    ),
    path("llms.txt", LLMSTextView.as_view()),
    path("llms_de.txt", TemplateView.as_view(template_name="llms_de.txt", content_type="text/plain")),
    path("llms_en.txt", TemplateView.as_view(template_name="llms_en.txt", content_type="text/plain")),
    path("llms_ru.txt", TemplateView.as_view(template_name="llms_ru.txt", content_type="text/plain")),
    path("llms_uk.txt", TemplateView.as_view(template_name="llms_uk.txt", content_type="text/plain")),
    path("api/", api.urls),
    path("u/<uuid:token>/", UnsubscribeView.as_view(), name="unsubscribe"),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("llms.txt", LLMSTextView.as_view()),
    path("accounts/", include("allauth.urls")),
    path("cabinet/", include("cabinet.urls")),
    path("system/", include("system.urls")),
    path("conversations/", include("features.conversations.urls")),
    path("", include("features.booking.urls")),
    path("", include("features.main.urls", namespace="main")),
    path("cabinet/tracking/", include("codex_django.tracking.urls")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

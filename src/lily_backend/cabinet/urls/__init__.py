from django.conf import settings
from django.urls import include, path

from .booking import booking_urlpatterns
from .campaigns import campaigns_urlpatterns
from .client import client_urlpatterns
from .conversations import conversations_urlpatterns
from .staff import staff_urlpatterns
from .system import system_urlpatterns

app_name = "cabinet"

urlpatterns = (
    system_urlpatterns
    + client_urlpatterns
    + booking_urlpatterns
    + conversations_urlpatterns
    + campaigns_urlpatterns
    + staff_urlpatterns
)

# External library routes
urlpatterns += [
    path("", include("codex_django.cabinet.urls")),
    path("", include("cabinet.auth_urls")),
]

# Optional Allauth integration
if getattr(settings, "CODEX_ALLAUTH_ENABLED", False):
    urlpatterns.insert(2, path("", include("allauth.urls")))

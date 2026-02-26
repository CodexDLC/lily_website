"""Cabinet URL configuration."""

from django.shortcuts import redirect
from django.urls import path

from .views.appointments import AppointmentsView
from .views.appointments_create import AppointmentCreateView
from .views.auth import CabinetLoginView, CabinetLogoutView, MagicLinkView
from .views.clients import ClientsView
from .views.dashboard import DashboardView
from .views.masters import MastersView
from .views.services import ServicesView
from .views.user_profile import ProfileView

app_name = "cabinet"

urlpatterns = [
    # Root → redirect to dashboard or login
    path(
        "",
        lambda request: redirect("cabinet:dashboard" if request.user.is_staff else "cabinet:appointments"),
        name="index",
    ),
    # Auth
    path("login/", CabinetLoginView.as_view(), name="login"),
    path("logout/", CabinetLogoutView.as_view(), name="logout"),
    path("magic/<str:token>/", MagicLinkView.as_view(), name="magic_link"),
    # Admin sections
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("appointments/", AppointmentsView.as_view(), name="appointments"),
    path("appointments/create/", AppointmentCreateView.as_view(), name="appointments_create"),
    path("clients/", ClientsView.as_view(), name="clients"),
    path("masters/", MastersView.as_view(), name="masters"),
    path("services/", ServicesView.as_view(), name="services"),
    # Client sections
    path("profile/", ProfileView.as_view(), name="profile"),
]

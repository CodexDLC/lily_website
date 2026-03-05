"""Cabinet URL configuration."""

from django.shortcuts import redirect
from django.urls import path

from .views.appointments import AppointmentsView
from .views.auth import CabinetLoginView, CabinetLogoutView, MagicLinkView
from .views.clients import ClientsView
from .views.constructor import AdminConstructorView
from .views.contacts import ContactRequestsView
from .views.dashboard import DashboardView
from .views.masters import MastersView
from .views.price_adjustment import AppointmentPriceEditView
from .views.reschedule import RescheduleAppointmentView
from .views.services import ServicesView
from .views.system_settings import SystemSettingsView
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
    path("clients/", ClientsView.as_view(), name="clients"),
    path("masters/", MastersView.as_view(), name="masters"),
    path("services/", ServicesView.as_view(), name="services"),
    path("contacts/", ContactRequestsView.as_view(), name="contacts"),
    # Client sections
    path("profile/", ProfileView.as_view(), name="profile"),
    # Reschedule flow via token (public with token logic)
    path("appointments/reschedule/<str:token>/", RescheduleAppointmentView.as_view(), name="reschedule_appointment"),
    # QR Price Edit link (Admin check is inside the view)
    path("appointment/<str:token>/edit-price/", AppointmentPriceEditView.as_view(), name="edit_price"),
    path("settings/", SystemSettingsView.as_view(), name="system_settings"),
    path("constructor/", AdminConstructorView.as_view(), name="constructor"),
]

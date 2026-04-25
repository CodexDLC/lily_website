from django.urls import path

from ..views.client import (
    ClientAppointmentsView,
    ClientCancelAppointmentView,
    ClientHomeView,
    ClientManageAppointmentView,
    ClientRescheduleConfirmView,
    ClientRescheduleModalView,
    ClientRescheduleSlotsView,
    ClientSettingsView,
)

client_urlpatterns = [
    path("my/", ClientHomeView.as_view(), name="client_home"),
    path("my/appointments/", ClientAppointmentsView.as_view(), name="client_appointments"),
    path(
        "my/appointments/manage/<str:token>/", ClientManageAppointmentView.as_view(), name="client_manage_appointment"
    ),
    path(
        "my/appointments/cancel/<str:token>/", ClientCancelAppointmentView.as_view(), name="client_cancel_appointment"
    ),
    path(
        "my/appointments/reschedule/<str:token>/", ClientRescheduleModalView.as_view(), name="client_reschedule_modal"
    ),
    path(
        "my/appointments/reschedule/<str:token>/slots/",
        ClientRescheduleSlotsView.as_view(),
        name="client_reschedule_slots",
    ),
    path(
        "my/appointments/reschedule/<str:token>/confirm/",
        ClientRescheduleConfirmView.as_view(),
        name="client_reschedule_confirm",
    ),
    path("my/settings/", ClientSettingsView.as_view(), name="settings"),
]

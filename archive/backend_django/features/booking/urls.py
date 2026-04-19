from django.urls import path

from .views.actions import (
    CancelAppointmentActionView,
    CancelAppointmentView,
    CancelSuccessView,
    ConfirmAppointmentView,
    RescheduleAppointmentView,
)
from .views.v2_wizard import BookingV2WizardView
from .views.wizard import BookingWizardView

app_name = "booking"

urlpatterns = [
    # V1 -- существующий мастер записи (не трогаем)
    path("booking/", BookingWizardView.as_view(), name="booking_wizard"),
    # V2 -- новый конструктор цепочек (HTMX)
    path("booking/v2/", BookingV2WizardView.as_view(), name="booking_v2_wizard"),
    # Email actions (confirm / cancel / reschedule)
    path("appointments/confirm/<uuid:token>/", ConfirmAppointmentView.as_view(), name="booking_confirm"),
    path("appointments/cancel/<uuid:token>/", CancelAppointmentView.as_view(), name="booking_cancel"),
    path(
        "appointments/cancel/<uuid:token>/action/", CancelAppointmentActionView.as_view(), name="booking_cancel_action"
    ),
    path("appointments/cancel/success/", CancelSuccessView.as_view(), name="booking_cancel_success"),
    path("appointments/reschedule/<uuid:token>/", RescheduleAppointmentView.as_view(), name="booking_reschedule"),
]

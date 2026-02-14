from django.urls import path

from .views.actions import (
    CancelAppointmentActionView,
    CancelAppointmentView,
    CancelSuccessView,
    ConfirmAppointmentView,
    RescheduleAppointmentView,
)
from .views.wizard import BookingWizardView

urlpatterns = [
    path("booking/", BookingWizardView.as_view(), name="booking_wizard"),
    # Placeholder URLs for email actions
    path("appointments/confirm/<uuid:token>/", ConfirmAppointmentView.as_view(), name="booking_confirm"),
    path("appointments/cancel/<uuid:token>/", CancelAppointmentView.as_view(), name="booking_cancel"),
    path(
        "appointments/cancel/<uuid:token>/action/", CancelAppointmentActionView.as_view(), name="booking_cancel_action"
    ),  # Для POST-запроса отмены
    path(
        "appointments/cancel/success/", CancelSuccessView.as_view(), name="booking_cancel_success"
    ),  # Страница успеха отмены
    path("appointments/reschedule/<uuid:token>/", RescheduleAppointmentView.as_view(), name="booking_reschedule"),
]

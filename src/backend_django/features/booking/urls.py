from django.urls import path

from .views.wizard import BookingWizardView

urlpatterns = [
    path("booking/", BookingWizardView.as_view(), name="booking_wizard"),
]

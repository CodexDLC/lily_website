from django.urls import path
from django.views.generic import RedirectView

app_name = "conversations"

urlpatterns = [
    path("contact/", RedirectView.as_view(pattern_name="main:contacts", permanent=True), name="contact"),
]

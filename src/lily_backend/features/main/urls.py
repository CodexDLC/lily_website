from django.urls import path
from features.conversations.views import ContactFormView

from .views import (
    BuchungsregelnView,
    DatenschutzView,
    FaqView,
    HomeView,
    ImpressumView,
    ServiceDetailView,
    ServicesIndexView,
    TeamView,
)

app_name = "main"

urlpatterns = [
    path("", HomeView.as_view(), name="index"),
    path("contacts/", ContactFormView.as_view(), name="contacts"),
    path("services/", ServicesIndexView.as_view(), name="services"),
    path("services/<slug:slug>/", ServiceDetailView.as_view(), name="service_detail"),
    path("team/", TeamView.as_view(), name="team"),
    path("impressum/", ImpressumView.as_view(), name="impressum"),
    path("datenschutz/", DatenschutzView.as_view(), name="datenschutz"),
    path("faq/", FaqView.as_view(), name="faq"),
    path("buchungsregeln/", BuchungsregelnView.as_view(), name="buchungsregeln"),
]

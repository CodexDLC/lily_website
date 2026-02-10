from django.urls import path
from django.views.generic import TemplateView

from .views import home, services

urlpatterns = [
    # Home
    path("", home.HomeView.as_view(), name="home"),
    # Services Index (Price List)
    path("services/", services.ServicesIndexView.as_view(), name="services"),
    # Service Detail (Dynamic by slug)
    path("services/<slug:slug>/", services.ServiceDetailView.as_view(), name="service_detail"),
    # Static Pages (Temporary TemplateViews until logic is added)
    path("team/", TemplateView.as_view(template_name="team/team.html"), name="team"),
    path("contacts/", TemplateView.as_view(template_name="contacts/contacts.html"), name="contacts"),
    # Legal
    path("impressum/", TemplateView.as_view(template_name="legal/impressum.html"), name="impressum"),
    path("datenschutz/", TemplateView.as_view(template_name="legal/datenschutz.html"), name="datenschutz"),
]

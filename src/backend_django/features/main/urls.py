from django.urls import path

from .views import contacts, home, legal, services, team

urlpatterns = [
    # Home
    path("", home.HomeView.as_view(), name="home"),
    # Services Index (Price List)
    path("services/", services.ServicesIndexView.as_view(), name="services"),
    # Service Detail (Dynamic by slug)
    path("services/<slug:slug>/", services.ServiceDetailView.as_view(), name="service_detail"),
    # Team
    path("team/", team.TeamView.as_view(), name="team"),
    # Contacts
    path("contacts/", contacts.ContactsView.as_view(), name="contacts"),
    # Legal
    path("impressum/", legal.ImpressumView.as_view(), name="impressum"),
    path("datenschutz/", legal.DatenschutzView.as_view(), name="datenschutz"),
    path("faq/", legal.FaqView.as_view(), name="faq"),
]

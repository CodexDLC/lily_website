import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404
from django.test import RequestFactory
from features.main.views import (
    BuchungsregelnView,
    DatenschutzView,
    FaqView,
    HomeView,
    ImpressumView,
    ServiceDetailView,
    ServicesIndexView,
    TeamView,
)


@pytest.fixture
def rf():
    return RequestFactory()


def add_session_to_request(request):
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()


@pytest.mark.django_db
class TestMainViews:
    def test_home_view(self, rf):
        request = rf.get("/")
        view = HomeView()
        view.request = request
        context = view.get_context_data()
        assert "bento" in context
        assert "team" in context

    def test_services_index_view(self, rf, service, master):
        service.masters.add(master)

        request = rf.get("/services/")
        add_session_to_request(request)
        view = ServicesIndexView()
        view.request = request
        context = view.get_context_data()
        assert "categories" in context
        assert "cart" in context
        assert service.category in context["categories"]

    def test_services_index_hides_categories_without_bookable_services(self, rf, category, service):
        request = rf.get("/services/")
        add_session_to_request(request)
        view = ServicesIndexView()
        view.request = request

        context = view.get_context_data()

        assert category not in context["categories"]

    def test_services_index_template_renders_search(self, client, service, master):
        service.masters.add(master)

        response = client.get("/de/services/")

        assert response.status_code == 200
        assert b"service-search-input" in response.content

    def test_service_detail_view_success(self, rf, service):
        request = rf.get(f"/services/{service.category.slug}/")
        add_session_to_request(request)
        view = ServiceDetailView()
        view.request = request
        view.kwargs = {"slug": service.category.slug}
        context = view.get_context_data()
        assert context["category"] == service.category
        assert "cart" in context

    def test_service_detail_view_404(self, rf):
        request = rf.get("/services/missing/")
        add_session_to_request(request)
        view = ServiceDetailView()
        view.request = request
        view.kwargs = {"slug": "missing"}
        with pytest.raises(Http404):
            view.get_context_data()

    def test_team_view(self, rf, master):
        request = rf.get("/team/")
        view = TeamView()
        view.request = request
        context = view.get_context_data()
        assert "team" in context

    def test_legal_views(self, rf):
        for view_class in [ImpressumView, DatenschutzView, FaqView, BuchungsregelnView]:
            view = view_class()
            assert view.template_name.startswith("features/main/legal/")

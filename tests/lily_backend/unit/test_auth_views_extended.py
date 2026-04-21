from unittest.mock import MagicMock, patch

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from src.lily_backend.cabinet.views.auth import AuthModeContextMixin, BrandedLoginView, BrandedLogoutView


@pytest.mark.unit
class TestAuthViewsExtended:
    def setup_method(self):
        self.factory = RequestFactory()

    def test_auth_mode_context_mixin(self):
        """Test AuthModeContextMixin adds settings to context."""

        class BaseView:
            def get_context_data(self, **kwargs):
                return kwargs

        class MockView(AuthModeContextMixin, BaseView):
            pass

        view = MockView()
        with patch("src.lily_backend.cabinet.views.auth.settings") as mock_settings:
            mock_settings.CODEX_AUTH_MODE = "test_mode"
            mock_settings.CODEX_AUTH_PROVIDER = "test_provider"
            mock_settings.CODEX_ALLAUTH_ENABLED = True

            context = view.get_context_data(existing="data")

            assert context["auth_mode"] == "test_mode"
            assert context["auth_provider"] == "test_provider"
            assert context["allauth_enabled"] is True
            assert context["existing"] == "data"

    def test_branded_login_view_success_url_allauth(self):
        """Test BrandedLoginView.get_success_url when allauth is enabled."""
        view = BrandedLoginView()
        view.request = self.factory.get("/login/")

        with patch("src.lily_backend.cabinet.views.auth.settings") as mock_settings:
            mock_settings.CODEX_ALLAUTH_ENABLED = True

            # Mock allauth adapter
            mock_adapter = MagicMock()
            mock_adapter.get_login_redirect_url.return_value = "/allauth/success/"

            with patch("allauth.account.adapter.get_adapter", return_value=mock_adapter):
                url = view.get_success_url()
                assert url == "/allauth/success/"

    def test_branded_logout_view_get_success_url(self):
        """Test BrandedLogoutView.get_success_url."""
        view = BrandedLogoutView()
        with patch("src.lily_backend.cabinet.views.auth.reverse_lazy", return_value="/login/"):
            url = view.get_success_url()
            assert url == "/login/"

    def test_branded_logout_view_post_htmx(self):
        """Test BrandedLogoutView.post with HTMX request."""
        view = BrandedLogoutView()
        request = self.factory.post("/logout/", HTTP_HX_REQUEST="true")

        # Mock super().post
        mock_response = HttpResponse()
        with (
            patch("django.contrib.auth.views.LogoutView.post", return_value=mock_response),
            patch.object(view, "get_success_url", return_value="/login/"),
        ):
            response = view.post(request)
            assert response["HX-Redirect"] == "/login/"

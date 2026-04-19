from unittest.mock import MagicMock, patch

import pytest
from system.views.errors import handler400, handler403, handler404, handler405, handler500


class TestSystemErrors:
    @pytest.fixture
    def mock_render(self):
        with patch("system.views.errors.render") as mock:
            mock.return_value = MagicMock()
            yield mock

    def test_handler400(self, mock_render):
        req = MagicMock()
        handler400(req, exception=None)
        mock_render.assert_called_once_with(req, "errors/400.html", status=400)

    def test_handler403(self, mock_render):
        req = MagicMock()
        handler403(req, exception=None)
        mock_render.assert_called_once_with(req, "errors/403.html", status=403)

    def test_handler404(self, mock_render):
        req = MagicMock()
        handler404(req, exception=None)
        mock_render.assert_called_once_with(req, "errors/404.html", status=404)

    def test_handler405(self, mock_render):
        req = MagicMock()
        handler405(req, exception=None)
        mock_render.assert_called_once_with(req, "errors/405.html", status=405)

    def test_handler500(self, mock_render):
        req = MagicMock()
        handler500(req)
        mock_render.assert_called_once_with(req, "errors/500.html", status=500)

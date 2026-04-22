from unittest.mock import patch

import pytest
from features.booking.dto.public_cart import PublicCart
from features.booking.views.public.cart import CartAddView, CartRemoveView, CartSetModeView, CartSetStageView
from tests.factories.main import ServiceFactory


@pytest.mark.django_db
class TestCartViews:
    @patch("features.booking.views.public.cart.get_cart")
    @patch("features.booking.views.public.cart.save_cart")
    @patch("features.booking.views.public.cart.render")
    def test_cart_add_view(self, mock_render, mock_save, mock_get, rf):
        service = ServiceFactory(name="Test Service")
        request = rf.post("/booking/cart/add/", {"service_id": str(service.pk)})
        request.session = {}
        cart = PublicCart()
        mock_get.return_value = cart

        view = CartAddView()
        view.request = request
        view.post(request)

        assert cart.has(service.pk)
        mock_save.assert_called_with(request, cart)
        mock_render.assert_called()

    @patch("features.booking.views.public.cart.get_cart")
    @patch("features.booking.views.public.cart.save_cart")
    @patch("features.booking.views.public.cart.render")
    def test_cart_remove_view(self, mock_render, mock_save, mock_get, rf):
        request = rf.post("/booking/cart/remove/", {"service_id": "1"})
        request.session = {}
        cart = PublicCart()
        mock_get.return_value = cart

        view = CartRemoveView()
        view.request = request
        view.post(request)

        mock_save.assert_called_with(request, cart)
        mock_render.assert_called()

    @patch("features.booking.views.public.cart.get_cart")
    @patch("features.booking.views.public.cart.save_cart")
    @patch("features.booking.views.public.cart.render")
    def test_cart_set_mode_view(self, mock_render, mock_save, mock_get, rf):
        request = rf.post("/booking/cart/mode/", {"mode": "multi_day"})
        request.session = {}
        cart = PublicCart()
        mock_get.return_value = cart

        view = CartSetModeView()
        view.request = request
        view.post(request)

        assert cart.mode == "multi_day"
        mock_save.assert_called_with(request, cart)

    @patch("features.booking.views.public.cart.get_cart")
    @patch("features.booking.views.public.cart.save_cart")
    @patch("features.booking.views.public.cart.render")
    def test_cart_set_stage_view(self, mock_render, mock_save, mock_get, rf):
        request = rf.post("/booking/cart/stage/", {"stage": "2"})
        request.session = {}
        cart = PublicCart()
        mock_get.return_value = cart

        view = CartSetStageView()
        view.request = request
        view.post(request)

        assert cart.stage == 2
        mock_save.assert_called_with(request, cart)

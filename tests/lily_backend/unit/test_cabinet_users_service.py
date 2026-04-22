from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from system.models import Client, UserProfile

from src.lily_backend.cabinet.services.users import UserService

User = get_user_model()


@pytest.mark.django_db
class TestUserService:
    def test_get_list_context_basic(self):
        req = HttpRequest()
        req.GET = {"segment": "all"}

        # Create some data
        User.objects.create(username="testuser", email="test@example.com")
        Client.objects.create(first_name="Ghost", last_name="Client", is_ghost=True)

        ctx = UserService.get_list_context(req)
        assert ctx["active_segment"] == "all"
        assert ctx["header_title"] == "Administration"
        assert "cards" in ctx
        assert len(ctx["cards"].items) >= 2

    def test_get_list_context_segments(self):
        for segment in ["clients", "shadows", "staff"]:
            req = HttpRequest()
            req.GET = {"segment": segment}
            ctx = UserService.get_list_context(req)
            assert ctx["active_segment"] == segment

    def test_get_client_detail_ghost(self):
        client = Client.objects.create(first_name="Ghost", last_name="Client", is_ghost=True)
        id_token = f"ghost_{client.pk}"

        res = UserService.get_client_detail(id_token)
        assert res["client"].pk == client.pk
        assert res["client"].first_name == "Ghost"

    def test_get_client_detail_user_no_client(self):
        user = User.objects.create(username="newuser", first_name="John", last_name="Doe", email="john@doe.com")
        id_token = f"user_{user.pk}"

        # Should create a new Client record
        res = UserService.get_client_detail(id_token)
        assert res["client"].user == user
        assert res["client"].first_name == "John"
        assert not res["client"].is_ghost
        assert Client.objects.filter(user=user).exists()

    def test_get_client_detail_user_gluing_email(self):
        # Orphan client
        orphan = Client.objects.create(first_name="Max", last_name="Mustermann", email="max@example.com", is_ghost=True)
        # Real user with same email
        user = User.objects.create(username="max", first_name="Max", last_name="M", email="max@example.com")

        id_token = f"user_{user.pk}"
        res = UserService.get_client_detail(id_token)

        assert res["client"].pk == orphan.pk
        assert res["client"].user == user
        assert not res["client"].is_ghost

    def test_get_client_detail_user_gluing_phone(self):
        user = User.objects.create(username="phoneuser")
        UserProfile.objects.create(user=user, phone="+123456789")
        # Orphan client with same phone
        orphan = Client.objects.create(first_name="Phone", last_name="Client", phone="+123456789", is_ghost=True)

        id_token = f"user_{user.pk}"
        res = UserService.get_client_detail(id_token)

        assert res["client"].pk == orphan.pk
        assert res["client"].user == user

    def test_get_client_detail_invalid_token(self):
        res = UserService.get_client_detail("invalid_123")
        assert res["client"] is None

    def test_get_client_detail_ghost_invalid_pk(self):
        # ValueError case
        res = UserService.get_client_detail("ghost_abc")
        assert res["client"] is None

    def test_get_client_detail_user_invalid_pk(self):
        # ValueError case
        res = UserService.get_client_detail("user_abc")
        assert res["client"] is None

    def test_get_client_detail_non_existent_ghost(self):
        res = UserService.get_client_detail("ghost_999999")
        assert res["client"] is None

    def test_get_client_detail_non_existent_user(self):
        res = UserService.get_client_detail("user_999999")
        assert res["client"] is None

    @patch("system.services.loyalty.LoyaltyService.get_display_for_profile")
    def test_loyalty_service_integration(self, mock_loyalty):
        mock_loyalty.return_value = MagicMock(staff_label="Gold")
        user = User.objects.create(username="loyaltyuser")
        id_token = f"user_{user.pk}"

        res = UserService.get_client_detail(id_token)
        assert res["loyalty"].staff_label == "Gold"
        mock_loyalty.assert_called_once()

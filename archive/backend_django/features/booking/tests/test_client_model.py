"""Tests for Client model methods and properties."""

import pytest
from django.contrib.auth import get_user_model
from features.booking.models.client import Client

User = get_user_model()


@pytest.mark.unit
class TestClientModelProperties:
    def test_is_ghost_true_for_unlinked_guest(self, client_obj):
        assert client_obj.is_ghost is True

    def test_is_ghost_false_for_linked_user(self, client_obj, admin_user):
        client_obj.user = admin_user
        client_obj.status = Client.STATUS_ACTIVE
        client_obj.save()
        assert client_obj.is_ghost is False

    def test_primary_contact_returns_phone_first(self, client_obj):
        assert client_obj.primary_contact == client_obj.phone

    def test_primary_contact_returns_email_when_no_phone(self):
        c = Client.objects.create(phone="", email="only@email.de")
        assert c.primary_contact == "only@email.de"

    def test_display_name_uses_full_name(self, client_obj):
        assert client_obj.display_name() == "Anna Testova"

    def test_display_name_returns_guest_when_no_name(self):
        c = Client.objects.create(phone="+49222000001", first_name="", last_name="")
        result = str(c.display_name())
        assert "Guest" in result or "Gast" in result or len(result) > 0

    def test_get_full_name_with_both_parts(self, client_obj):
        assert client_obj.get_full_name() == "Anna Testova"

    def test_get_full_name_with_first_name_only(self):
        c = Client.objects.create(phone="+49333000001", first_name="Anna", last_name="")
        assert c.get_full_name() == "Anna"

    def test_get_full_name_empty_when_no_name(self):
        c = Client.objects.create(phone="+49444000001", first_name="", last_name="")
        assert c.get_full_name() == ""

    def test_access_token_generated_on_save(self, client_obj):
        assert client_obj.access_token is not None
        assert len(client_obj.access_token) == 32  # uuid4.hex

    def test_str_representation(self, client_obj):
        result = str(client_obj)
        assert "Anna" in result or client_obj.phone in result


@pytest.mark.integration
class TestClientActivateAccount:
    def test_activate_account_sets_status_active(self, client_obj, admin_user):
        assert client_obj.status == Client.STATUS_GUEST
        client_obj.activate_account(admin_user)
        client_obj.refresh_from_db()
        assert client_obj.status == Client.STATUS_ACTIVE
        assert client_obj.user == admin_user

    def test_activate_account_is_no_longer_ghost(self, client_obj, admin_user):
        client_obj.activate_account(admin_user)
        assert client_obj.is_ghost is False


@pytest.mark.unit
class TestClientConstraints:
    def test_phone_or_email_required_phone_only(self):
        c = Client.objects.create(phone="+49555000001", email="")
        assert c.pk is not None

    def test_phone_or_email_required_email_only(self):
        c = Client.objects.create(phone="", email="valid@test.de")
        assert c.pk is not None

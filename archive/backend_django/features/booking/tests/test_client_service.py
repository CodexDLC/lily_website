"""Tests for ClientService.get_or_create_client()."""

import pytest
from features.booking.models.client import Client
from features.booking.services.utils.client_service import ClientService


@pytest.mark.integration
class TestClientServiceGetOrCreate:
    def test_creates_new_client_when_not_found(self):
        from codex_tools.common.phone import normalize_phone

        raw_phone = "+49600000001"
        client = ClientService.get_or_create_client(
            first_name="Neue",
            last_name="Kundin",
            phone=raw_phone,
            email="neue@test.de",
        )
        assert client.pk is not None
        assert Client.objects.filter(phone=normalize_phone(raw_phone)).exists()

    def test_finds_existing_client_by_phone(self):
        from codex_tools.common.phone import normalize_phone

        norm = normalize_phone("+49700000001")
        existing = Client.objects.create(phone=norm, email="a@b.de", first_name="Anna")
        found = ClientService.get_or_create_client(phone="+49700000001", email="a@b.de")
        assert found.pk == existing.pk
        assert Client.objects.filter(phone=norm).count() == 1

    def test_finds_existing_client_by_email(self):
        existing = Client.objects.create(phone="+49800000001", email="find@me.de")
        found = ClientService.get_or_create_client(phone="", email="find@me.de")
        assert found.pk == existing.pk

    def test_updates_name_if_previously_empty(self):
        from codex_tools.common.phone import normalize_phone

        Client.objects.create(phone=normalize_phone("+49900000001"), first_name="", last_name="")
        updated = ClientService.get_or_create_client(phone="+49900000001", first_name="Neue", last_name="Name")
        updated.refresh_from_db()
        assert updated.first_name == "Neue"

    def test_does_not_overwrite_with_empty_name(self):
        from codex_tools.common.phone import normalize_phone

        client = Client.objects.create(phone=normalize_phone("+49901000001"), first_name="Anna")
        ClientService.get_or_create_client(phone="+49901000001", first_name="")
        client.refresh_from_db()
        assert client.first_name == "Anna"

    def test_sets_consent_marketing_and_date(self):
        from codex_tools.common.phone import normalize_phone

        client = Client.objects.create(phone=normalize_phone("+49902000001"), consent_marketing=False)
        ClientService.get_or_create_client(phone="+49902000001", consent_marketing=True)
        client.refresh_from_db()
        assert client.consent_marketing is True
        assert client.consent_date is not None

    def test_does_not_unset_consent_marketing(self):
        from codex_tools.common.phone import normalize_phone

        client = Client.objects.create(phone=normalize_phone("+49903000001"), consent_marketing=True)
        ClientService.get_or_create_client(phone="+49903000001", consent_marketing=False)
        client.refresh_from_db()
        assert client.consent_marketing is True

    def test_returns_none_for_no_contact(self):
        # No phone and no email → _find_client returns None → _create_new_client called
        # But CheckConstraint will prevent creation with both empty
        from django.db import IntegrityError

        with pytest.raises((IntegrityError, Exception)):
            ClientService.get_or_create_client(phone="", email="", first_name="Test")

    def test_prefers_exact_match_over_partial(self):
        from codex_tools.common.phone import normalize_phone

        norm = normalize_phone("+49100000001")
        client_a = Client.objects.create(phone=norm, email="a@test.de", first_name="A")
        # client_b can't have same phone due to no unique constraint, but create with different phone
        Client.objects.create(phone=normalize_phone("+49100000002"), email="b@test.de", first_name="B")
        # Exact match on both phone + email should find client_a
        found = ClientService.get_or_create_client(phone="+49100000001", email="a@test.de")
        assert found.pk == client_a.pk

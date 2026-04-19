"""Tests for cabinet appointments: permissions (admin, master, client) and HTMX GET forms."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from features.booking.models import Appointment
from features.booking.models.client import Client
from features.booking.models.master import Master
from features.main.models.category import Category
from features.main.models.service import Service

User = get_user_model()

pytestmark = pytest.mark.django_db

APPOINTMENTS_URL = reverse("cabinet:appointments")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="perm_admin",
        email="perm_admin@example.com",
        password="pw",  # pragma: allowlist secret
    )


@pytest.fixture
def master_user(db):
    user = User.objects.create_user(
        username="perm_master",
        email="perm_master@example.com",
        password="pw",  # pragma: allowlist secret
    )
    Master.objects.create(user=user, name="Master A", slug="master-a")
    return user


@pytest.fixture
def other_master_user(db):
    user = User.objects.create_user(
        username="perm_other_master",
        email="perm_other@example.com",
        password="pw",  # pragma: allowlist secret
    )
    Master.objects.create(user=user, name="Master B", slug="master-b")
    return user


@pytest.fixture
def client_user(db):
    """Regular user with Client profile but no Master profile."""
    user = User.objects.create_user(
        username="perm_client",
        email="perm_client@example.com",
        password="pw",  # pragma: allowlist secret
    )
    Client.objects.create(user=user, phone="+49000000000", first_name="Client User")
    return user


@pytest.fixture
def _service(db):
    cat = Category.objects.create(title="Perm Cat", slug="perm-cat", is_active=True)
    return Service.objects.create(category=cat, title="Perm Svc", price=50.00, duration=60, is_active=True)


@pytest.fixture
def test_client_obj(db):
    return Client.objects.create(
        first_name="Anna",
        last_name="Test",
        email="anna@test.local",
        phone="+49111111111",
    )


@pytest.fixture
def pending_appointment(master_user, _service, test_client_obj):
    """Pending appointment assigned to master_user's Master profile."""
    return Appointment.objects.create(
        client=test_client_obj,
        service=_service,
        master=master_user.master_profile,
        datetime_start=timezone.now() + timedelta(days=1),
        duration_minutes=60,
        price=50.00,
        status=Appointment.STATUS_PENDING,
    )


@pytest.fixture
def confirmed_appointment(pending_appointment):
    pending_appointment.status = Appointment.STATUS_CONFIRMED
    pending_appointment.save(update_fields=["status"])
    return pending_appointment


@pytest.fixture
def other_master_appointment(other_master_user, _service, test_client_obj):
    """Pending appointment assigned to OTHER master."""
    return Appointment.objects.create(
        client=test_client_obj,
        service=_service,
        master=other_master_user.master_profile,
        datetime_start=timezone.now() + timedelta(days=2),
        duration_minutes=60,
        price=50.00,
        status=Appointment.STATUS_PENDING,
    )


@pytest.fixture
def mock_arq():
    with patch("core.arq.client.DjangoArqClient.enqueue_job") as m:
        yield m


# ---------------------------------------------------------------------------
# 1. Permission tests
# ---------------------------------------------------------------------------


class TestAppointmentsPermissions:
    """Who can POST actions to AppointmentsView."""

    def test_anonymous_cannot_post(self, client, pending_appointment):
        resp = client.post(APPOINTMENTS_URL, {"action": "approve", "id": pending_appointment.id})
        assert resp.status_code == 302
        assert "/login" in resp.url or "/accounts/login" in resp.url

    def test_admin_can_approve(self, client, admin_user, pending_appointment, mock_arq):
        client.force_login(admin_user)
        resp = client.post(APPOINTMENTS_URL, {"action": "approve", "id": pending_appointment.id})
        assert resp.status_code == 200
        pending_appointment.refresh_from_db()
        assert pending_appointment.status == Appointment.STATUS_CONFIRMED

    def test_master_can_approve_own(self, client, master_user, pending_appointment, mock_arq):
        client.force_login(master_user)
        resp = client.post(APPOINTMENTS_URL, {"action": "approve", "id": pending_appointment.id})
        assert resp.status_code == 200
        pending_appointment.refresh_from_db()
        assert pending_appointment.status == Appointment.STATUS_CONFIRMED

    def test_master_cannot_approve_others(self, client, master_user, other_master_appointment, mock_arq):
        client.force_login(master_user)
        resp = client.post(APPOINTMENTS_URL, {"action": "approve", "id": other_master_appointment.id})
        assert resp.status_code == 403

    def test_client_cannot_approve(self, client, client_user, pending_appointment, mock_arq):
        client.force_login(client_user)
        resp = client.post(APPOINTMENTS_URL, {"action": "approve", "id": pending_appointment.id})
        assert resp.status_code == 403

    def test_master_can_complete_own(self, client, master_user, confirmed_appointment, mock_arq):
        client.force_login(master_user)
        resp = client.post(APPOINTMENTS_URL, {"action": "complete", "id": confirmed_appointment.id})
        assert resp.status_code == 200
        confirmed_appointment.refresh_from_db()
        assert confirmed_appointment.status == Appointment.STATUS_COMPLETED

    def test_master_cannot_complete_others(self, client, master_user, other_master_appointment, mock_arq):
        other_master_appointment.status = Appointment.STATUS_CONFIRMED
        other_master_appointment.save(update_fields=["status"])
        client.force_login(master_user)
        resp = client.post(APPOINTMENTS_URL, {"action": "complete", "id": other_master_appointment.id})
        assert resp.status_code == 403

    def test_admin_can_cancel(self, client, admin_user, confirmed_appointment, mock_arq):
        client.force_login(admin_user)
        resp = client.post(
            APPOINTMENTS_URL,
            {"action": "cancel", "id": confirmed_appointment.id, "reason_code": "other", "reason_text": "Test"},
        )
        assert resp.status_code == 200
        confirmed_appointment.refresh_from_db()
        assert confirmed_appointment.status == Appointment.STATUS_CANCELLED


# ---------------------------------------------------------------------------
# 2. Smoke tests for HTMX GET forms
# ---------------------------------------------------------------------------


class TestHtmxGetForms:
    """GET actions that return HTMX partial forms should return 200 for admin."""

    def test_confirm_form(self, client, admin_user, pending_appointment):
        client.force_login(admin_user)
        resp = client.get(APPOINTMENTS_URL, {"action": "confirm_form", "id": pending_appointment.id})
        assert resp.status_code == 200
        assert b"approve" in resp.content

    def test_cancel_form(self, client, admin_user, pending_appointment):
        client.force_login(admin_user)
        resp = client.get(APPOINTMENTS_URL, {"action": "cancel_form", "id": pending_appointment.id})
        assert resp.status_code == 200

    def test_complete_form(self, client, admin_user, confirmed_appointment):
        client.force_login(admin_user)
        resp = client.get(APPOINTMENTS_URL, {"action": "complete_form", "id": confirmed_appointment.id})
        assert resp.status_code == 200

    def test_reschedule_form(self, client, admin_user, pending_appointment, mock_arq):
        client.force_login(admin_user)
        resp = client.get(APPOINTMENTS_URL, {"action": "reschedule_form", "id": pending_appointment.id})
        assert resp.status_code == 200

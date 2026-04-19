"""Tests for every action that sends an email: cabinet actions + booking receipt."""

import asyncio
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
import requests  # type: ignore[import-untyped]
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from features.booking.models import Appointment
from features.booking.models.client import Client
from features.booking.models.master import Master
from features.main.models.category import Category
from features.main.models.service import Service

from src.workers.notification_worker.services.notification_service import NotificationService

User = get_user_model()

MAILPIT_API = "http://localhost:8025/api/v1"
TEMPLATES_DIR = str(Path(__file__).resolve().parents[4] / "workers" / "templates")

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class MailpitHelper:
    def get_messages(self) -> dict:
        return requests.get(f"{MAILPIT_API}/messages", timeout=5).json()

    def get_last(self) -> dict | None:
        msgs = self.get_messages()
        if msgs.get("total", 0) == 0:
            return None
        return msgs["messages"][0]


async def _wait_for_mail(mailpit: MailpitHelper, timeout: float = 3.0) -> dict:
    """Poll Mailpit until an email arrives or timeout expires."""
    elapsed = 0.0
    while elapsed < timeout:
        msg = mailpit.get_last()
        if msg:
            return msg
        await asyncio.sleep(0.5)
        elapsed += 0.5
    raise AssertionError(f"No email received in Mailpit within {timeout}s")


def _make_email_data(appt: Appointment) -> dict:
    """Build a context dict suitable for NotificationService.send_notification()."""
    local_dt = timezone.localtime(appt.datetime_start)
    client_name = appt.client.first_name
    return {
        "id": appt.id,
        "first_name": client_name,
        "client_name": appt.client.get_full_name() or client_name,
        "client_email": appt.client.email,
        "client_phone": appt.client.phone,
        "service_name": appt.service.title,
        "master_name": appt.master.name,
        "datetime": local_dt.strftime("%d.%m.%Y %H:%M"),
        "date": local_dt.strftime("%d.%m.%Y"),
        "time": local_dt.strftime("%H:%M"),
        "duration_minutes": appt.duration_minutes,
        "price": float(appt.price),
        # Template-specific rendering fields
        "email_tag": "TEST",
        "greeting": f"Hallo {client_name},",
        "email_body": "Dies ist eine Test-Nachricht.",
        "email_button_text": "Termin bestätigen",
        "reason_text": "Test-Stornierungsgrund.",
        "signature": "Ihr LILY Beauty Team",
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin_notif",
        email="admin_notif@example.com",
        password="pw",  # pragma: allowlist secret
    )


@pytest.fixture
def appt(db):
    client = Client.objects.create(
        first_name="Anna",
        last_name="Muster",
        email="testclient@mailpit.local",
        phone="+49123456789",
    )
    cat = Category.objects.create(title="Maniküre", slug="manikure-test", is_active=True)
    svc = Service.objects.create(category=cat, title="Gel-Lack", price=45.00, duration=60, is_active=True)
    master_user = User.objects.create_user(
        username="master_notif",
        email="master_notif@example.com",
        password="pw",  # pragma: allowlist secret
    )
    # Исправлено: имя поля 'user'
    master = Master.objects.create(user=master_user, name="Lena", slug="lena")
    return Appointment.objects.create(
        client=client,
        service=svc,
        master=master,
        datetime_start=timezone.now() + timedelta(days=1),
        duration_minutes=60,
        price=45.00,
        status=Appointment.STATUS_PENDING,
    )


@pytest.fixture
def appt_confirmed(appt):
    appt.status = Appointment.STATUS_CONFIRMED
    appt.save(update_fields=["status"])
    return appt


@pytest.fixture
def mock_arq():
    """Patch ARQ enqueue so tests need no Redis."""
    with patch("core.arq.client.DjangoArqClient.enqueue_job") as mock_enqueue:
        yield mock_enqueue


@pytest.fixture
def mailpit():
    """Clear Mailpit inbox before each test and return a helper."""
    requests.delete(f"{MAILPIT_API}/messages", timeout=5)
    return MailpitHelper()


@pytest.fixture
def notification_svc():
    """Worker's NotificationService wired to Mailpit SMTP on localhost:1025."""
    return NotificationService(
        templates_dir=TEMPLATES_DIR,
        site_url="http://localhost:8000",
        smtp_host="localhost",
        smtp_port=1025,
        smtp_from_email="test@lily-salon.de",
        smtp_use_tls=False,
    )


# ---------------------------------------------------------------------------
# Class 1: Cabinet view action tests — no Redis, no Mailpit required
# ---------------------------------------------------------------------------


class TestCabinetViewActions:
    """POST to cabinet appointments view — verify status changes and ARQ calls."""

    def _post(self, django_client, admin_user, data):
        django_client.force_login(admin_user)
        return django_client.post(reverse("cabinet:appointments"), data=data)

    def test_approve_sets_confirmed(self, client, admin_user, appt, mock_arq):
        response = self._post(client, admin_user, {"action": "approve", "id": appt.id})
        assert response.status_code == 200
        appt.refresh_from_db()
        assert appt.status == Appointment.STATUS_CONFIRMED
        assert mock_arq.called

    def test_cancel_sets_cancelled(self, client, admin_user, appt_confirmed, mock_arq):
        response = self._post(
            client,
            admin_user,
            {
                "action": "cancel",
                "id": appt_confirmed.id,
                "reason_code": "other",
                "reason_text": "Test",
            },
        )
        assert response.status_code == 200
        appt_confirmed.refresh_from_db()
        assert appt_confirmed.status == Appointment.STATUS_CANCELLED

    def test_no_show_sets_no_show(self, client, admin_user, appt_confirmed, mock_arq):
        response = self._post(client, admin_user, {"action": "no_show", "id": appt_confirmed.id})
        assert response.status_code == 200
        appt_confirmed.refresh_from_db()
        assert appt_confirmed.status == Appointment.STATUS_NO_SHOW


# ---------------------------------------------------------------------------
# Class 2: Real email delivery tests — require Mailpit on localhost:1025/8025
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestEmailDelivery:
    """
    Call worker's NotificationService directly → SMTP → Mailpit.

    Prerequisites:
        - Mailpit running: SMTP on localhost:1025, API on localhost:8025
        - No Redis needed (notifications are sent synchronously)

    Run:
        pytest -m integration
    Skip:
        pytest -m "not integration"
    """

    async def test_bk_receipt(self, notification_svc, mailpit, appt):
        data = _make_email_data(appt)
        await notification_svc.send_notification(
            appt.client.email,
            "Buchungsanfrage erhalten - LILY Beauty Salon",
            "bk_receipt",
            data,
        )
        msg = await _wait_for_mail(mailpit)
        assert msg["Subject"] == "Buchungsanfrage erhalten - LILY Beauty Salon"
        assert appt.client.email in msg["To"][0]["Address"]

    async def test_bk_confirmation(self, notification_svc, mailpit, appt):
        data = _make_email_data(appt)
        await notification_svc.send_notification(
            appt.client.email,
            "Terminbestätigung - LILY Beauty Salon",
            "bk_confirmation",
            data,
        )
        msg = await _wait_for_mail(mailpit)
        assert msg["Subject"] == "Terminbestätigung - LILY Beauty Salon"
        assert appt.client.email in msg["To"][0]["Address"]

    async def test_bk_cancellation(self, notification_svc, mailpit, appt):
        data = _make_email_data(appt)
        await notification_svc.send_notification(
            appt.client.email,
            "Terminstornierung - LILY Beauty Salon",
            "bk_cancellation",
            data,
        )
        msg = await _wait_for_mail(mailpit)
        assert msg["Subject"] == "Terminstornierung - LILY Beauty Salon"
        assert appt.client.email in msg["To"][0]["Address"]

    async def test_bk_no_show(self, notification_svc, mailpit, appt):
        data = _make_email_data(appt)
        await notification_svc.send_notification(
            appt.client.email,
            "Vermisster Termin - LILY Beauty Salon",
            "bk_no_show",
            data,
        )
        msg = await _wait_for_mail(mailpit)
        assert msg["Subject"] == "Vermisster Termin - LILY Beauty Salon"
        assert appt.client.email in msg["To"][0]["Address"]

    async def test_bk_reschedule(self, notification_svc, mailpit, appt):
        data = _make_email_data(appt)
        await notification_svc.send_notification(
            appt.client.email,
            "Terminvorschlag - LILY Beauty Salon",
            "bk_reschedule",
            data,
        )
        msg = await _wait_for_mail(mailpit)
        assert msg["Subject"] == "Terminvorschlag - LILY Beauty Salon"
        assert appt.client.email in msg["To"][0]["Address"]

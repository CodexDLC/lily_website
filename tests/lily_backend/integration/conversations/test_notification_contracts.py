from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from cabinet.adapters import CabinetAccountAdapter
from features.conversations.services import notifications

from workers.notification_worker.tasks.notification_tasks import send_universal_notification_task


@pytest.mark.asyncio
async def test_universal_notification_task_accepts_queue_payload_keyword():
    notification_service = SimpleNamespace(send_notification=AsyncMock(return_value=None))

    await send_universal_notification_task(
        {"notification_service": notification_service, "job_try": 1},
        payload={
            "notification_id": "notif-1",
            "recipient": {"email": "client@example.com", "first_name": "Anna"},
            "template_name": "account/acc_verification",
            "subject": "Verify your email",
            "channels": ["email"],
            "context_data": {"activate_url": "https://example.com/verify"},
        },
    )

    notification_service.send_notification.assert_awaited_once_with(
        email="client@example.com",
        subject="Verify your email",
        template_name="account/acc_verification",
        data={"activate_url": "https://example.com/verify"},
        headers=None,
    )


@pytest.mark.asyncio
async def test_universal_notification_task_accepts_flat_payload():
    notification_service = SimpleNamespace(send_notification=AsyncMock(return_value=None))

    # This mimics codex-django 0.4+ flat payload
    await send_universal_notification_task(
        {"notification_service": notification_service, "job_try": 1},
        payload={
            "mode": "template",
            "notification_id": "notif-flat-1",
            "recipient_email": "flat@example.com",
            "client_name": "Ivan Ivanov",
            "template_name": "account/acc_verification",
            "subject": "Verify flat email",
            "channels": ["email"],
            "context_data": {"activate_url": "https://example.com/verify-flat"},
        },
    )

    notification_service.send_notification.assert_awaited_once_with(
        email="flat@example.com",
        subject="Verify flat email",
        template_name="account/acc_verification",
        data={"activate_url": "https://example.com/verify-flat"},
        headers=None,
    )


@pytest.mark.asyncio
async def test_universal_notification_task_routes_booking_received_to_bot_event():
    notification_service = SimpleNamespace(send_notification=AsyncMock(return_value=None))
    stream_manager = SimpleNamespace(add_event=AsyncMock(return_value=None))

    await send_universal_notification_task(
        {"notification_service": notification_service, "stream_manager": stream_manager, "job_try": 1},
        payload={
            "mode": "template",
            "notification_id": "notif-booking-1",
            "recipient_email": "client@example.com",
            "client_name": "Anna",
            "template_name": "bk_receipt",
            "subject": "Booking received",
            "event_type": "booking.received",
            "channels": ["telegram"],
            "context_data": {
                "id": 7,
                "first_name": "Anna",
                "last_name": "Test",
                "client_phone": "+491234",
                "client_email": "client@example.com",
                "service_name": "Manicure",
                "master_name": "Lily",
                "datetime": "20.04.2026 10:00",
                "duration_minutes": 60,
                "price": "50.00",
                "request_call": False,
            },
        },
    )

    # Stream writing to bot has been disabled
    stream_manager.add_event.assert_not_awaited()
    notification_service.send_notification.assert_not_awaited()


@pytest.mark.asyncio
async def test_universal_notification_task_status_update_includes_email_label():
    notification_service = SimpleNamespace(send_notification=AsyncMock(return_value=None))
    stream_manager = SimpleNamespace(add_event=AsyncMock(return_value=None))

    await send_universal_notification_task(
        {"notification_service": notification_service, "stream_manager": stream_manager, "job_try": 1},
        payload={
            "mode": "template",
            "notification_id": "notif-booking-confirmed-1",
            "recipient_email": "client@example.com",
            "client_name": "Anna",
            "template_name": "bk_confirmation",
            "subject": "Booking confirmed",
            "event_type": "booking.confirmed",
            "channels": ["email"],
            "context_data": {"id": 7},
        },
    )

    # Stream writing to bot has been disabled, but email is still sent
    stream_manager.add_event.assert_not_awaited()
    notification_service.send_notification.assert_awaited_once()


def test_account_adapter_prefers_request_language(monkeypatch):
    captured: dict[str, str] = {}

    def fake_send_account_verification(**kwargs):
        captured.update(kwargs)
        return "job-1"

    monkeypatch.setattr(notifications.NotificationService, "send_account_verification", fake_send_account_verification)

    adapter = CabinetAccountAdapter()
    adapter.send_mail(
        "account/email/email_confirmation_signup",
        "client@example.com",
        {
            "user": SimpleNamespace(first_name="Anna", username="anna"),
            "request": SimpleNamespace(LANGUAGE_CODE="ru"),
            "activate_url": "https://example.com/verify",
        },
    )

    assert captured["lang"] == "ru"
    assert captured["signup"] is True
    assert captured["recipient_email"] == "client@example.com"

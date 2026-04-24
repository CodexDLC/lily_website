import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from arq import Retry

from src.workers.notification_worker.schemas import NotificationPayload
from src.workers.notification_worker.tasks.notification_tasks import (
    BotPayloadEnricher,
    _mailbox_headers,
    _notification_label,
    _stream_event_type,
    expire_reservation_task,
    requeue_event_task,
    send_group_booking_notification_task,
    send_universal_notification_task,
)


@pytest.fixture
def mock_ctx():
    mock_redis = MagicMock()
    mock_redis.string.get = AsyncMock()
    return {
        "notification_service": MagicMock(send_notification=AsyncMock()),
        "redis_service": mock_redis,
        "stream_manager": MagicMock(add_event=AsyncMock()),
        "job_try": 1,
    }


class TestBotPayloadEnricher:
    def test_enrich_basic(self):
        payload = NotificationPayload(
            notification_id="123",
            recipient={"email": "test@example.com", "first_name": "Anna"},
            context_data={"service_name": "Wash", "price": 50.0},
        )
        result = BotPayloadEnricher.enrich(payload)
        assert result["client_email"] == "test@example.com"
        assert result["service_name"] == "Wash"
        assert result["price"] == "50.0"

    def test_enrich_group_booking(self):
        payload = NotificationPayload(
            notification_id="123",
            recipient={"first_name": "Anna"},
            context_data={
                "items": [{"service_name": "Wash", "master_name": "M1"}, {"service_name": "Cut", "master_name": "M1"}],
                "total_price": 100.0,
            },
        )
        result = BotPayloadEnricher.enrich(payload)
        assert result["service_name"] == "Wash, Cut"
        assert result["master_name"] == "M1"
        assert result["price"] == "100.0"

    def test_enricher_with_items_no_service_name(self):
        payload = MagicMock()
        payload.context_data = {
            "items": [{"service_name": "S1", "master_name": "M1"}, {"service_name": "S2", "master_name": "M1"}]
        }
        payload.recipient.first_name = "Anna"
        payload.recipient.last_name = "L"

        enriched = BotPayloadEnricher.enrich(payload)
        assert enriched["service_name"] == "S1, S2"
        assert enriched["master_name"] == "M1"


def test_helpers():
    assert _mailbox_headers({"thread_key": "xyz"})["X-Lily-Thread-Key"] == "xyz"
    assert _mailbox_headers({}) is None
    assert _stream_event_type("booking.received") == "new_appointment"
    assert _notification_label("booking.confirmed", None) == "Подтверждение записи"


class TestUniversalTask:
    @pytest.mark.asyncio
    async def test_missing_payload(self, mock_ctx):
        await send_universal_notification_task(mock_ctx, payload=None)
        mock_ctx["notification_service"].send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_validation_failed(self, mock_ctx):
        await send_universal_notification_task(mock_ctx, payload={"invalid": "data"})
        mock_ctx["notification_service"].send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_email_only_success(self, mock_ctx):
        payload = {
            "notification_id": "nt_1",
            "recipient_email": "client@example.com",
            "client_name": "Anna",
            "template_name": "bk_confirmation",
            "channels": ["email"],
            "context_data": {"id": 10},
        }
        await send_universal_notification_task(mock_ctx, payload=payload)
        mock_ctx["notification_service"].send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_failure(self, mock_ctx):
        payload = {
            "notification_id": "nt_1",
            "recipient_email": "client@example.com",
            "channels": ["email"],
            "template_name": "bk_confirmation",
            "context_data": {"id": 10},
        }
        mock_ctx["notification_service"].send_notification.side_effect = Exception("SMTP fail")
        with pytest.raises(Retry):
            await send_universal_notification_task(mock_ctx, payload=payload)

    @pytest.mark.asyncio
    async def test_payload_dict_fallback(self, mock_ctx):
        payload = {
            "notification_id": "nt_dict",
            "recipient_email": "dict@example.com",
            "template_name": "bk_confirmation",
            "channels": ["email"],
            "context_data": {"id": 11},
        }
        await send_universal_notification_task(mock_ctx, payload_dict=payload)
        mock_ctx["notification_service"].send_notification.assert_called_once()


class TestNotificationHelpers:
    def test_notification_label_mapping(self):
        from src.workers.notification_worker.tasks.notification_tasks import _notification_label

        assert _notification_label("booking.received", None) == "Заявка получена"
        assert _notification_label(None, "bk_receipt") == "Заявка получена"
        assert _notification_label(None, "unknown") == "Письмо клиенту"

    def test_stream_event_type_fallback(self):
        from src.workers.notification_worker.tasks.notification_tasks import _stream_event_type

        assert _stream_event_type("booking.received") == "new_appointment"
        assert _stream_event_type("other") == "other"
        assert _stream_event_type(None) == ""


class TestLegacyTasks:
    @pytest.mark.asyncio
    async def test_send_group_booking_json_error(self, mock_ctx):
        from src.workers.notification_worker.tasks.notification_tasks import send_group_booking_notification_task

        mock_ctx["redis_service"].string.get.return_value = "invalid-json"
        await send_group_booking_notification_task(mock_ctx, group_id=123)
        mock_ctx["notification_service"].send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_group_booking_email_failure(self, mock_ctx):
        from src.workers.notification_worker.tasks.notification_tasks import send_group_booking_notification_task

        data = {"client_email": "a@b.com"}
        mock_ctx["redis_service"].string.get.return_value = json.dumps(data)
        mock_ctx["notification_service"].send_notification.side_effect = Exception("SMTP fail")
        with pytest.raises(Retry):
            await send_group_booking_notification_task(mock_ctx, group_id=1)

    @pytest.mark.asyncio
    async def test_send_booking_notification_missing_cache(self, mock_ctx):
        from src.workers.notification_worker.tasks.notification_tasks import send_booking_notification_task

        mock_ctx["redis_service"].string.get.return_value = None
        await send_booking_notification_task(mock_ctx, appointment_id=456)
        mock_ctx["notification_service"].send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_booking_notification_email_failure(self, mock_ctx):
        from src.workers.notification_worker.tasks.notification_tasks import send_booking_notification_task

        data = {"client_email": "a@b.com"}
        mock_ctx["redis_service"].string.get.return_value = json.dumps(data)
        mock_ctx["notification_service"].send_notification.side_effect = Exception("SMTP fail")
        with pytest.raises(Retry):
            await send_booking_notification_task(mock_ctx, appointment_id=1)

    @pytest.mark.asyncio
    async def test_send_contact_notification_missing_cache(self, mock_ctx):
        from src.workers.notification_worker.tasks.notification_tasks import send_contact_notification_task

        mock_ctx["redis_service"].string.get.return_value = None
        await send_contact_notification_task(mock_ctx, request_id=789)

    @pytest.mark.asyncio
    async def test_stream_sending_failure(self, mock_ctx):
        payload = {
            "notification_id": "nt_1",
            "recipient_email": "client@example.com",
            "channels": ["telegram"],
            "event_type": "booking.received",
            "context_data": {"id": 10},
        }
        mock_ctx["stream_manager"].add_event.side_effect = Exception("Redis fail")
        # Should not raise
        await send_universal_notification_task(mock_ctx, payload=payload)

    @pytest.mark.asyncio
    async def test_booking_notification_task(self, mock_ctx):
        from src.workers.notification_worker.tasks.notification_tasks import send_booking_notification_task

        mock_ctx["redis_service"].string.get.return_value = json.dumps({"client_email": "a@b.com"})
        await send_booking_notification_task(mock_ctx, 1)
        mock_ctx["notification_service"].send_notification.assert_called()

    @pytest.mark.asyncio
    async def test_contact_notification_task(self, mock_ctx):
        from src.workers.notification_worker.tasks.notification_tasks import send_contact_notification_task

        mock_ctx["redis_service"].string.get.return_value = json.dumps({"name": "A"})
        await send_contact_notification_task(mock_ctx, 1)
        mock_ctx["stream_manager"].add_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_requeue_and_expire(self, mock_ctx):
        await requeue_event_task(mock_ctx, {})
        await expire_reservation_task(mock_ctx, 1)


class TestGroupBookingTask:
    @pytest.mark.asyncio
    async def test_success(self, mock_ctx):
        data = {
            "group_id": 1,
            "client_name": "Group Client",
            "client_email": "group@test.com",
            "booking_date": "19.04.2026 10:00",
            "items": [{"master_name": "M1"}],
        }
        mock_ctx["redis_service"].string.get.return_value = json.dumps(data)
        await send_group_booking_notification_task(mock_ctx, 1)
        mock_ctx["notification_service"].send_notification.assert_called()

    @pytest.mark.asyncio
    async def test_cache_missing(self, mock_ctx):
        mock_ctx["redis_service"].string.get.return_value = None
        await send_group_booking_notification_task(mock_ctx, 1)
        mock_ctx["notification_service"].send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_redis_failure(self, mock_ctx):
        mock_ctx["redis_service"].string.get.side_effect = Exception("Redis down")
        # Should catch and raise Retry
        with pytest.raises(Retry):
            await send_group_booking_notification_task(mock_ctx, 1)
        mock_ctx["notification_service"].send_notification.assert_not_called()


class TestUtils:
    @pytest.mark.asyncio
    async def test_send_status_update_no_id(self, mock_ctx):
        from src.workers.notification_worker.tasks.utils import send_status_update

        await send_status_update(mock_ctx, None, "email", "success")
        mock_ctx["stream_manager"].add_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_status_update_no_manager(self, mock_ctx):
        from src.workers.notification_worker.tasks.utils import send_status_update

        ctx = mock_ctx.copy()
        ctx["stream_manager"] = None
        await send_status_update(ctx, 1, "email", "success")
        # Should log warning but not raise

    @pytest.mark.asyncio
    async def test_send_status_update_failure(self, mock_ctx):
        from src.workers.notification_worker.tasks.utils import send_status_update

        mock_ctx["stream_manager"].add_event.side_effect = Exception("Redis fail")
        await send_status_update(mock_ctx, 1, "email", "success")
        # Should catch and log error

    @pytest.mark.asyncio
    async def test_send_status_update_success(self, mock_ctx):
        from src.workers.notification_worker.tasks.utils import send_status_update

        await send_status_update(mock_ctx, 1, "email", "success")
        mock_ctx["stream_manager"].add_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_status_update_with_extras(self, mock_ctx):
        from src.workers.notification_worker.tasks.utils import send_status_update

        await send_status_update(
            mock_ctx,
            1,
            "email",
            "success",
            event_type="test_event",
            template_name="test_tpl",
            notification_label="test_label",
        )
        call_args = mock_ctx["stream_manager"].add_event.call_args[0][1]
        assert call_args["event_type"] == "test_event"
        assert call_args["template_name"] == "test_tpl"
        assert call_args["notification_label"] == "test_label"

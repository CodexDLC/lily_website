import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.workers.notification_worker.tasks.message_tasks import send_message_task, send_appointment_notification

@pytest.mark.asyncio
async def test_send_message_task_success():
    ctx = {
        "orchestrator": AsyncMock(),
        "settings": MagicMock(),
    }
    ctx["orchestrator"].send_message.return_value = True
    ctx["settings"].TWILIO_WHATSAPP_TEMPLATE_SID = "tpl123"
    
    with patch("src.workers.notification_worker.tasks.message_tasks._send_status_update", new_callable=AsyncMock) as mock_status:
        await send_message_task(ctx, "+49123456", "Hello", appointment_id=123)
        
        mock_status.assert_called_with(ctx, 123, "twilio", "success")
        ctx["orchestrator"].send_message.assert_called_once()
        args, kwargs = ctx["orchestrator"].send_message.call_args
        assert kwargs["wa_template_sid"] == "tpl123"

@pytest.mark.asyncio
async def test_send_message_task_failure():
    ctx = {
        "orchestrator": AsyncMock(),
        "settings": MagicMock(),
    }
    ctx["orchestrator"].send_message.return_value = False
    
    with patch("src.workers.notification_worker.tasks.message_tasks._send_status_update", new_callable=AsyncMock) as mock_status:
        await send_message_task(ctx, "+49123456", "Hello")
        mock_status.assert_called_with(ctx, None, "twilio", "failed")

@pytest.mark.asyncio
async def test_send_message_task_missing_orchestrator():
    ctx = {}
    with patch("src.workers.notification_worker.tasks.message_tasks._send_status_update", new_callable=AsyncMock) as mock_status:
        await send_message_task(ctx, "+49123456", "Hello")
        mock_status.assert_called_with(ctx, None, "twilio", "failed")

@pytest.mark.asyncio
async def test_send_appointment_notification_full_flow():
    ctx = {
        "arq_service": AsyncMock(),
        "notification_service": MagicMock(),
    }
    appointment_data = {
        "client_email": "client@example.com",
        "client_phone": "+49123",
        "first_name": "Anna",
        "datetime": "20.10.2024 10:00"
    }
    ctx["notification_service"].get_sms_text.return_value = "Sms Text"
    ctx["notification_service"].get_absolute_logo_url.return_value = "http://logo"
    
    await send_appointment_notification(ctx, "confirmed", 123, appointment_data)
    
    # Check email enqueued
    ctx["arq_service"].enqueue_job.assert_any_call(
        "send_email_task",
        recipient_email="client@example.com",
        subject="Appointment Confirmed - Lily Beauty",
        template_name="appointment_confirmed.html",
        data=appointment_data,
        appointment_id=123
    )
    # Check message enqueued
    ctx["arq_service"].enqueue_job.assert_any_call(
        "send_message_task",
        phone_number="+49123",
        message="Sms Text",
        appointment_id=123,
        media_url="http://logo",
        variables={
            "1": "Anna",
            "2": "20.10.2024",
            "3": "10:00",
            "4": "123"
        }
    )

@pytest.mark.asyncio
async def test_send_appointment_notification_date_parsing_fallback():
    ctx = {
        "arq_service": AsyncMock(),
        "notification_service": MagicMock(),
    }
    appointment_data = {
        "client_phone": "+49123",
        "datetime": "2024-10-20 (unexpected format)"
    }
    await send_appointment_notification(ctx, "confirmed", 1, appointment_data)
    
    # Finding the call for send_message_task
    found = False
    for call in ctx["arq_service"].enqueue_job.call_args_list:
        if call.args[0] == "send_message_task":
            found = True
            vars = call.kwargs["variables"]
            assert vars["2"] == "2024-10-20" # fallback to split[0]
    assert found

@pytest.mark.asyncio
async def test_send_appointment_notification_no_contacts():
    ctx = {
        "arq_service": AsyncMock(),
        "notification_service": MagicMock(),
    }
    await send_appointment_notification(ctx, "rescheduled", 456, {})
    ctx["arq_service"].enqueue_job.assert_not_called()

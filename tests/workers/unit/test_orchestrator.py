from unittest.mock import AsyncMock, MagicMock

import pytest

from src.workers.core.base_module.orchestrator import NotificationOrchestrator


@pytest.fixture
def mock_email_client():
    client = AsyncMock()
    client.smtp_from_email = "smtp@test.com"
    return client


@pytest.fixture
def mock_seven_io_client():
    return AsyncMock()


@pytest.fixture
def mock_twilio_client():
    # Note: send_whatsapp_template and send_sms/whatsapp in orchestrator.py are called WITHOUT await
    # but the orchestrator calls them... wait, let me re-check if they are async.
    # Looking at orchestrator.py:
    # line 50: return await self.twilio_client.send_email(...) -> ASYNC
    # line 90: success = self.twilio_client.send_whatsapp_template(...) -> SYNC??
    # line 92: success = self.twilio_client.send_whatsapp(...) -> SYNC??
    # line 99: return self.twilio_client.send_sms(...) -> SYNC??
    #
    # If they are sync, I'll use MagicMock.
    return MagicMock()


@pytest.fixture
def orchestrator(mock_email_client, mock_seven_io_client, mock_twilio_client):
    return NotificationOrchestrator(mock_email_client, mock_seven_io_client, mock_twilio_client)


@pytest.mark.asyncio
class TestOrchestratorEmail:
    async def test_send_email_primary_success(self, orchestrator, mock_email_client):
        res = await orchestrator.send_email("to@test.com", "Sub", "Html")
        assert res is True
        mock_email_client.send_email.assert_called_once()

    async def test_send_email_fallback_success(self, orchestrator, mock_email_client, mock_twilio_client):
        mock_email_client.send_email.side_effect = Exception("SMTP Down")
        mock_twilio_client.send_email = AsyncMock(return_value=True)

        res = await orchestrator.send_email("to@test.com", "Sub", "Html")
        assert res is True
        mock_email_client.send_email.assert_called_once()
        mock_twilio_client.send_email.assert_called_once()

    async def test_send_email_all_failed(self, orchestrator, mock_email_client, mock_twilio_client):
        mock_email_client.send_email.side_effect = Exception("SMTP Down")
        mock_twilio_client.send_email = AsyncMock(return_value=False)

        res = await orchestrator.send_email("to@test.com", "Sub", "Html")
        assert res is False


@pytest.mark.asyncio
class TestOrchestratorMessage:
    async def test_send_message_seven_io_whatsapp_success(self, orchestrator, mock_seven_io_client):
        mock_seven_io_client.send_whatsapp.return_value = True
        res = await orchestrator.send_message("123", "Hello")
        assert res is True
        mock_seven_io_client.send_whatsapp.assert_called_once()

    async def test_send_message_seven_io_sms_fallback(self, orchestrator, mock_seven_io_client):
        mock_seven_io_client.send_whatsapp.return_value = False
        mock_seven_io_client.send_sms.return_value = True
        res = await orchestrator.send_message("123", "Hello")
        assert res is True
        mock_seven_io_client.send_whatsapp.assert_called_once()
        mock_seven_io_client.send_sms.assert_called_once()

    async def test_send_message_twilio_wa_fallback(self, orchestrator, mock_seven_io_client, mock_twilio_client):
        mock_seven_io_client.send_whatsapp.return_value = False
        mock_seven_io_client.send_sms.return_value = False
        mock_twilio_client.send_whatsapp.return_value = True

        res = await orchestrator.send_message("123", "Hello")
        assert res is True
        mock_twilio_client.send_whatsapp.assert_called_once()

    async def test_send_message_twilio_wa_template_fallback(
        self, orchestrator, mock_seven_io_client, mock_twilio_client
    ):
        mock_seven_io_client.send_whatsapp.return_value = False
        mock_seven_io_client.send_sms.return_value = False
        mock_twilio_client.send_whatsapp_template.return_value = True

        res = await orchestrator.send_message("123", "Hello", wa_template_sid="SID", wa_variables={"v": 1})
        assert res is True
        mock_twilio_client.send_whatsapp_template.assert_called_once()

    async def test_send_message_twilio_sms_last_resort(self, orchestrator, mock_seven_io_client, mock_twilio_client):
        mock_seven_io_client.send_whatsapp.return_value = False
        mock_seven_io_client.send_sms.return_value = False
        mock_twilio_client.send_whatsapp.return_value = False
        mock_twilio_client.send_sms.return_value = True

        res = await orchestrator.send_message("123", "Hello")
        assert res is True
        mock_twilio_client.send_sms.assert_called_once()

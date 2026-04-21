from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.workers.core.base_module.twilio_service import TwilioService


@pytest.fixture
def twilio_service():
    return TwilioService(
        account_sid="ACxxx",
        auth_token="auth",
        from_number="+123456",
        sendgrid_api_key="SG.xxx",  # pragma: allowlist secret
    )


def test_format_phone(twilio_service):
    assert twilio_service._format_phone("+49 123-456") == "+49123456"
    assert twilio_service._format_phone("0123456") == "+49123456"
    assert twilio_service._format_phone("123456") == "+123456"


def test_send_sms_success(twilio_service):
    with patch.object(twilio_service, "client") as mock_client:
        mock_messages = mock_client.messages
        mock_sent = MagicMock(sid="SMxxx")
        mock_messages.create.return_value = mock_sent

        res = twilio_service.send_sms("+49123", "Hello")
        assert res is True
        mock_messages.create.assert_called_once()


def test_send_sms_failure(twilio_service):
    with patch.object(twilio_service, "client") as mock_client:
        mock_client.messages.create.side_effect = Exception("Twilio Down")
        res = twilio_service.send_sms("+49123", "Hello")
        assert res is False


def test_send_whatsapp_template_success(twilio_service):
    with patch.object(twilio_service, "client") as mock_client:
        mock_messages = mock_client.messages
        mock_sent = MagicMock(sid="WAxxx")
        mock_messages.create.return_value = mock_sent

        res = twilio_service.send_whatsapp_template("+49123", "HXxxx", {"foo": "bar"})
        assert res is True
        kwargs = mock_messages.create.call_args[1]
        assert kwargs["content_sid"] == "HXxxx"


def test_send_whatsapp_freeform_with_media(twilio_service):
    with patch.object(twilio_service, "client") as mock_client:
        mock_messages = mock_client.messages
        mock_messages.create.return_value = MagicMock(sid="WAxxx")

        media_url = "https://example.com/image.jpg"
        res = twilio_service.send_whatsapp("+49123", "Hello", media_url=media_url)
        assert res is True
        kwargs = mock_messages.create.call_args[1]
        assert kwargs["media_url"] == [media_url]


@pytest.mark.asyncio
async def test_send_email_success(twilio_service):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=202)
        res = await twilio_service.send_email("to@test.com", "Sub", "Html", "from@test.com")
        assert res is True


@pytest.mark.asyncio
async def test_send_email_no_key():
    service = TwilioService("AC", "auth", "+1", sendgrid_api_key=None)
    res = await service.send_email("to", "sub", "html", "from")
    assert res is False

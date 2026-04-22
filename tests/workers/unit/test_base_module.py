"""Unit tests for workers/core/base_module: AsyncEmailClient, SevenIOClient,
TwilioService, NotificationOrchestrator.

All HTTP calls and Twilio SDK calls are mocked — no network required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── AsyncEmailClient ──────────────────────────────────────────────────────────


@pytest.mark.unit
class TestAsyncEmailClient:
    def _client(self, *, sendgrid_key: str | None = None):
        from workers.core.base_module.email_client import AsyncEmailClient

        return AsyncEmailClient(
            smtp_host="smtp.test",
            smtp_port=587,
            smtp_user="user",
            smtp_password="pass",  # pragma: allowlist secret
            smtp_from_email="noreply@test.com",
            sendgrid_api_key=sendgrid_key,
        )

    async def test_send_email_smtp_success(self):
        client = self._client()
        with patch("workers.core.base_module.email_client.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await client.send_email("to@test.com", "Subject", "<p>Hi</p>")
            mock_send.assert_called_once()

    async def test_send_email_smtp_failure_no_sendgrid_raises(self):
        client = self._client()
        with (
            patch("workers.core.base_module.email_client.aiosmtplib.send", side_effect=OSError("SMTP down")),
            pytest.raises(OSError),
        ):
            await client.send_email("to@test.com", "Subject", "<p>Hi</p>")

    async def test_send_email_smtp_failure_sendgrid_fallback_success(self, httpx_mock):
        httpx_mock.add_response(status_code=202)
        client = self._client(sendgrid_key="SG.KEY")
        with patch("workers.core.base_module.email_client.aiosmtplib.send", side_effect=OSError("SMTP down")):
            await client.send_email("to@test.com", "Subject", "<p>Hi</p>")

    async def test_send_email_smtp_failure_sendgrid_failure_raises(self, httpx_mock):
        httpx_mock.add_response(status_code=500, text="Error")
        client = self._client(sendgrid_key="SG.KEY")
        with (
            patch("workers.core.base_module.email_client.aiosmtplib.send", side_effect=OSError("SMTP down")),
            pytest.raises(RuntimeError, match="SendGrid API error"),
        ):
            await client.send_email("to@test.com", "Subject", "<p>Hi</p>")

    async def test_send_via_smtp_uses_ssl_for_port_465(self):
        from workers.core.base_module.email_client import AsyncEmailClient

        client = AsyncEmailClient(smtp_host="smtp.test", smtp_port=465, smtp_from_email="f@test.com")
        with patch("workers.core.base_module.email_client.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await client._send_via_smtp("to@t.com", "S", "<p></p>", 10)
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["use_tls"] is True
            assert call_kwargs["start_tls"] is False

    async def test_send_via_smtp_uses_starttls_for_port_587(self):
        client = self._client()
        with patch("workers.core.base_module.email_client.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await client._send_via_smtp("to@t.com", "S", "<p></p>", 10)
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["start_tls"] is True
            assert call_kwargs["use_tls"] is False

    async def test_send_via_smtp_without_credentials_omits_auth(self):
        from workers.core.base_module.email_client import AsyncEmailClient

        client = AsyncEmailClient(smtp_host="smtp.test", smtp_port=25, smtp_from_email="f@t.com")
        with patch("workers.core.base_module.email_client.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await client._send_via_smtp("to@t.com", "S", "<p></p>", 10)
            call_kwargs = mock_send.call_args[1]
            assert "username" not in call_kwargs

    async def test_send_via_sendgrid_with_headers(self, httpx_mock):
        httpx_mock.add_response(status_code=202)
        client = self._client(sendgrid_key="SG.KEY")
        await client._send_via_sendgrid("to@t.com", "S", "<p></p>", headers={"X-Token": "abc"})

    async def test_send_via_sendgrid_error_raises(self, httpx_mock):
        httpx_mock.add_response(status_code=400, text="bad request")
        client = self._client(sendgrid_key="SG.KEY")
        with pytest.raises(Exception, match="SendGrid API error"):
            await client._send_via_sendgrid("to@t.com", "S", "<p></p>")


# ── SevenIOClient ─────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestSevenIOClient:
    def _client(self):
        from workers.core.base_module.seven_io_client import SevenIOClient

        return SevenIOClient(api_key="TESTKEY", from_name="LILY")  # pragma: allowlist secret

    async def test_send_sms_success_100(self, httpx_mock):
        httpx_mock.add_response(json={"success": "100"})
        client = self._client()
        result = await client.send_sms("+49111222333", "Hello")
        assert result is True

    async def test_send_sms_success_true(self, httpx_mock):
        httpx_mock.add_response(json={"success": True})
        client = self._client()
        result = await client.send_sms("+49111222333", "Hello")
        assert result is True

    async def test_send_sms_messages_success(self, httpx_mock):
        httpx_mock.add_response(json={"messages": [{"success": True}]})
        client = self._client()
        result = await client.send_sms("+49111222333", "Hello")
        assert result is True

    async def test_send_sms_failure_returns_false(self, httpx_mock):
        httpx_mock.add_response(json={"success": "900", "messages": []})
        client = self._client()
        result = await client.send_sms("+49111222333", "Hello")
        assert result is False

    async def test_send_sms_exception_returns_false(self, httpx_mock):
        httpx_mock.add_exception(OSError("network error"))
        client = self._client()
        result = await client.send_sms("+49111222333", "Hello")
        assert result is False

    async def test_send_whatsapp_success(self, httpx_mock):
        httpx_mock.add_response(json={"success": True})
        client = self._client()
        result = await client.send_whatsapp("+49111222333", "Hello WA")
        assert result is True

    async def test_send_whatsapp_status_success(self, httpx_mock):
        httpx_mock.add_response(json={"status": "success"})
        client = self._client()
        result = await client.send_whatsapp("+49111222333", "Hello WA")
        assert result is True

    async def test_send_whatsapp_failure_returns_false(self, httpx_mock):
        httpx_mock.add_response(json={"error": "bad"})
        client = self._client()
        result = await client.send_whatsapp("+49111222333", "Hello WA")
        assert result is False

    async def test_send_whatsapp_exception_returns_false(self, httpx_mock):
        httpx_mock.add_exception(OSError("network error"))
        client = self._client()
        result = await client.send_whatsapp("+49111222333", "Hello WA")
        assert result is False


# ── TwilioService ─────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestTwilioService:
    def _make_client(self, sendgrid_key: str | None = "SG.KEY"):
        from workers.core.base_module.twilio_service import TwilioService

        with patch("workers.core.base_module.twilio_service.Client") as mock_twilio:
            svc = TwilioService(
                account_sid="ACtest",
                auth_token="token",
                from_number="+49000000000",
                sendgrid_api_key=sendgrid_key,
            )
            svc.client = mock_twilio.return_value
            return svc

    def test_format_phone_e164_passthrough(self):
        svc = self._make_client()
        assert svc._format_phone("+49111222333") == "+49111222333"

    def test_format_phone_leading_zero_to_e164(self):
        svc = self._make_client()
        assert svc._format_phone("0111222333") == "+49111222333"

    def test_format_phone_no_plus_adds_plus(self):
        svc = self._make_client()
        assert svc._format_phone("49111222333") == "+49111222333"

    def test_is_valid_media_url_none_false(self):
        svc = self._make_client()
        assert svc._is_valid_media_url(None) is False

    def test_is_valid_media_url_empty_false(self):
        svc = self._make_client()
        assert svc._is_valid_media_url("") is False

    def test_is_valid_media_url_localhost_false(self):
        svc = self._make_client()
        assert svc._is_valid_media_url("http://localhost/image.jpg") is False

    def test_is_valid_media_url_backend_false(self):
        svc = self._make_client()
        assert svc._is_valid_media_url("http://backend/image.jpg") is False

    def test_is_valid_media_url_public_true(self):
        svc = self._make_client()
        assert svc._is_valid_media_url("https://cdn.example.com/image.jpg") is True

    def test_send_sms_success(self):
        svc = self._make_client()
        svc.client.messages.create.return_value = MagicMock(sid="SM123")
        result = svc.send_sms("+49111222333", "Test SMS")
        assert result is True

    def test_send_sms_twilio_exception_returns_false(self):
        from twilio.base.exceptions import TwilioRestException

        svc = self._make_client()
        svc.client.messages.create.side_effect = TwilioRestException(status=400, uri="/uri", msg="Bad")
        result = svc.send_sms("+49111222333", "Test SMS")
        assert result is False

    def test_send_sms_generic_exception_returns_false(self):
        svc = self._make_client()
        svc.client.messages.create.side_effect = RuntimeError("unexpected")
        result = svc.send_sms("+49111222333", "Test SMS")
        assert result is False

    def test_send_whatsapp_template_success(self):
        svc = self._make_client()
        svc.client.messages.create.return_value = MagicMock(sid="SM456")
        result = svc.send_whatsapp_template("+49111222333", "HXsid", {"1": "value"})
        assert result is True

    def test_send_whatsapp_template_twilio_error_returns_false(self):
        from twilio.base.exceptions import TwilioRestException

        svc = self._make_client()
        svc.client.messages.create.side_effect = TwilioRestException(status=400, uri="/uri", msg="Bad")
        result = svc.send_whatsapp_template("+49111222333", "HXsid", {"1": "value"})
        assert result is False

    def test_send_whatsapp_freeform_success(self):
        svc = self._make_client()
        svc.client.messages.create.return_value = MagicMock(sid="SM789")
        result = svc.send_whatsapp("+49111222333", "Hello WA")
        assert result is True

    def test_send_whatsapp_with_valid_media_url(self):
        svc = self._make_client()
        svc.client.messages.create.return_value = MagicMock(sid="SM789")
        result = svc.send_whatsapp("+49111222333", "Hello", media_url="https://cdn.example.com/img.jpg")
        assert result is True
        call_kwargs = svc.client.messages.create.call_args[1]
        assert "media_url" in call_kwargs

    def test_send_whatsapp_invalid_media_url_skipped(self):
        svc = self._make_client()
        svc.client.messages.create.return_value = MagicMock(sid="SM789")
        svc.send_whatsapp("+49111222333", "Hello", media_url="http://localhost/img.jpg")
        call_kwargs = svc.client.messages.create.call_args[1]
        assert "media_url" not in call_kwargs

    def test_send_whatsapp_twilio_error_returns_false(self):
        from twilio.base.exceptions import TwilioRestException

        svc = self._make_client()
        svc.client.messages.create.side_effect = TwilioRestException(status=400, uri="/uri", msg="Bad")
        result = svc.send_whatsapp("+49111222333", "Hello")
        assert result is False

    async def test_send_email_no_sendgrid_key_returns_false(self):
        svc = self._make_client(sendgrid_key=None)
        result = await svc.send_email("to@test.com", "Sub", "<p></p>", from_email="f@t.com")
        assert result is False

    async def test_send_email_sendgrid_success(self, httpx_mock):
        httpx_mock.add_response(status_code=202)
        svc = self._make_client(sendgrid_key="SG.KEY")
        result = await svc.send_email("to@test.com", "Sub", "<p></p>", from_email="f@t.com")
        assert result is True

    async def test_send_email_sendgrid_error_returns_false(self, httpx_mock):
        httpx_mock.add_response(status_code=500, text="error")
        svc = self._make_client(sendgrid_key="SG.KEY")
        result = await svc.send_email("to@test.com", "Sub", "<p></p>", from_email="f@t.com")
        assert result is False

    async def test_send_email_sendgrid_exception_returns_false(self, httpx_mock):
        httpx_mock.add_exception(OSError("network"))
        svc = self._make_client(sendgrid_key="SG.KEY")
        result = await svc.send_email("to@test.com", "Sub", "<p></p>", from_email="f@t.com")
        assert result is False


# ── NotificationOrchestrator ──────────────────────────────────────────────────


@pytest.mark.unit
class TestNotificationOrchestrator:
    def _make_orchestrator(self):
        from workers.core.base_module.orchestrator import NotificationOrchestrator

        email_client = MagicMock()
        email_client.smtp_from_email = "noreply@test.com"
        email_client.send_email = AsyncMock()

        seven_io = MagicMock()
        seven_io.send_whatsapp = AsyncMock()
        seven_io.send_sms = AsyncMock()

        twilio = MagicMock()
        twilio.send_email = AsyncMock()
        twilio.send_whatsapp = MagicMock()
        twilio.send_whatsapp_template = MagicMock()
        twilio.send_sms = MagicMock()

        orch = NotificationOrchestrator(email_client, seven_io, twilio)
        return orch, email_client, seven_io, twilio

    async def test_send_email_smtp_success(self):
        orch, email_client, _, __ = self._make_orchestrator()
        result = await orch.send_email("to@test.com", "Sub", "<p></p>")
        assert result is True
        email_client.send_email.assert_called_once()

    async def test_send_email_smtp_fails_sendgrid_succeeds(self):
        orch, email_client, _, twilio = self._make_orchestrator()
        email_client.send_email.side_effect = OSError("SMTP down")
        twilio.send_email.return_value = True

        result = await orch.send_email("to@test.com", "Sub", "<p></p>")
        assert result is True
        twilio.send_email.assert_called_once()

    async def test_send_email_smtp_fails_custom_from_email_passed(self):
        orch, email_client, _, twilio = self._make_orchestrator()
        email_client.send_email.side_effect = OSError("SMTP down")
        twilio.send_email.return_value = True

        await orch.send_email("to@test.com", "Sub", "<p></p>", from_email="custom@from.com")
        call_kwargs = twilio.send_email.call_args[1]
        assert call_kwargs.get("from_email") == "custom@from.com"

    async def test_send_message_seven_io_wa_success(self):
        orch, _, seven_io, twilio = self._make_orchestrator()
        seven_io.send_whatsapp.return_value = True

        result = await orch.send_message("+49111", "Hello")
        assert result is True
        seven_io.send_whatsapp.assert_called_once()
        seven_io.send_sms.assert_not_called()

    async def test_send_message_seven_io_wa_fails_sms_succeeds(self):
        orch, _, seven_io, twilio = self._make_orchestrator()
        seven_io.send_whatsapp.return_value = False
        seven_io.send_sms.return_value = True

        result = await orch.send_message("+49111", "Hello")
        assert result is True
        seven_io.send_sms.assert_called_once()
        twilio.send_whatsapp.assert_not_called()

    async def test_send_message_seven_io_both_fail_twilio_wa_succeeds(self):
        orch, _, seven_io, twilio = self._make_orchestrator()
        seven_io.send_whatsapp.return_value = False
        seven_io.send_sms.return_value = False
        twilio.send_whatsapp.return_value = True

        result = await orch.send_message("+49111", "Hello")
        assert result is True
        twilio.send_whatsapp.assert_called_once()
        twilio.send_sms.assert_not_called()

    async def test_send_message_twilio_wa_template_when_sid_provided(self):
        orch, _, seven_io, twilio = self._make_orchestrator()
        seven_io.send_whatsapp.return_value = False
        seven_io.send_sms.return_value = False
        twilio.send_whatsapp_template.return_value = True

        result = await orch.send_message("+49111", "Hello", wa_template_sid="HXsid", wa_variables={"1": "val"})
        assert result is True
        twilio.send_whatsapp_template.assert_called_once()
        twilio.send_whatsapp.assert_not_called()

    async def test_send_message_all_fail_returns_false(self):
        orch, _, seven_io, twilio = self._make_orchestrator()
        seven_io.send_whatsapp.return_value = False
        seven_io.send_sms.return_value = False
        twilio.send_whatsapp.return_value = False
        twilio.send_sms.return_value = False

        result = await orch.send_message("+49111", "Hello")
        assert result is False
        twilio.send_sms.assert_called_once()

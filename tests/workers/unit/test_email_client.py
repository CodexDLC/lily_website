from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.workers.core.base_module.email_client import AsyncEmailClient


@pytest.fixture
def email_client():
    return AsyncEmailClient(
        smtp_host="smtp.test.com",
        smtp_port=587,
        smtp_user="user",
        smtp_password="password",  # pragma: allowlist secret
        smtp_from_email="lily@test.com",
        sendgrid_api_key="SG.xxx",  # pragma: allowlist secret
    )


@pytest.mark.asyncio
async def test_send_email_smtp_success(email_client):
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await email_client.send_email("to@test.com", "Subject", "<h1>Content</h1>")
        mock_send.assert_called_once()
        # Verify From/To/Subject
        msg = mock_send.call_args[0][0]
        assert msg["From"] == "lily@test.com"
        assert msg["To"] == "to@test.com"
        assert msg["Subject"] == "Subject"


@pytest.mark.asyncio
async def test_send_email_smtp_fail_sendgrid_success(email_client):
    with (
        patch("aiosmtplib.send", side_effect=Exception("SMTP Down")),
        patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
    ):
        mock_post.return_value = MagicMock(status_code=202)
        await email_client.send_email("to@test.com", "Subject", "<h1>Content</h1>")
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_all_fail(email_client):
    with (
        patch("aiosmtplib.send", side_effect=Exception("SMTP Down")),
        patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
    ):
        mock_post.return_value = MagicMock(status_code=500, text="Internal Error")
        with pytest.raises(RuntimeError, match="SendGrid API error"):
            await email_client.send_email("to@test.com", "Subject", "<h1>Content</h1>")


@pytest.mark.asyncio
async def test_send_email_no_sendgrid_key_fail():
    client = AsyncEmailClient("host", 587, sendgrid_api_key=None)
    with patch("aiosmtplib.send", side_effect=Exception("SMTP Down")), pytest.raises(Exception, match="SMTP Down"):
        await client.send_email("to@test.com", "Subject", "<h1>Content</h1>")


@pytest.mark.asyncio
async def test_smtp_ssl_port(email_client):
    email_client.smtp_port = 465
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await email_client._send_via_smtp("to@test.com", "Sub", "Html", 10)
        kwargs = mock_send.call_args[1]
        assert kwargs["use_tls"] is True
        assert kwargs["start_tls"] is False

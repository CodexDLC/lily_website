from email.message import EmailMessage
from typing import Any

import aiosmtplib
import httpx
from loguru import logger


class AsyncEmailClient:
    """
    Клиент для отправки Email с двойной страховкой:
    1. Попытка через SMTP.
    2. Если SMTP недоступен — попытка через SendGrid HTTP API.
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        smtp_from_email: str | None = None,
        smtp_use_tls: bool = False,
        sendgrid_api_key: str | None = None,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from_email = smtp_from_email
        self.smtp_use_tls = smtp_use_tls
        self.sendgrid_api_key = sendgrid_api_key
        self.sendgrid_url = "https://api.sendgrid.com/v3/mail/send"

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        timeout: int = 15,
        headers: dict[str, str] | None = None,
    ):
        """
        Main method for sending email. Tries SMTP first, then SendGrid.
        """
        smtp_error = None
        try:
            await self._send_via_smtp(to_email, subject, html_content, timeout, headers=headers)
            return
        except Exception as e:
            smtp_error = e
            logger.warning(f"SMTP failed to {to_email}: {e}. Trying SendGrid fallback...")

        if self.sendgrid_api_key:
            try:
                await self._send_via_sendgrid(to_email, subject, html_content, headers=headers)
                return
            except Exception as sg_e:
                logger.error(f"SendGrid fallback also failed to {to_email}: {sg_e}")
                raise sg_e from smtp_error
        else:
            logger.error(f"SMTP failed and no SendGrid API key provided for {to_email}")
            if smtp_error:
                raise smtp_error
            raise Exception("Email delivery failed: No SMTP success and no SendGrid key")

    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        timeout: int,
        headers: dict[str, str] | None = None,
    ):
        message = EmailMessage()
        message["From"] = self.smtp_from_email
        message["To"] = to_email
        message["Subject"] = subject
        for key, value in (headers or {}).items():
            if value:
                message[key] = value
        message.set_content("Please enable HTML to view this email.")
        message.add_alternative(html_content, subtype="html")

        use_ssl = self.smtp_port == 465
        start_tls = self.smtp_port == 587 or (self.smtp_use_tls and self.smtp_port != 465)

        send_kwargs: dict[str, Any] = {
            "hostname": self.smtp_host,
            "port": self.smtp_port,
            "use_tls": use_ssl,
            "start_tls": start_tls,
            "timeout": timeout,
        }

        if self.smtp_user and self.smtp_password:
            send_kwargs["username"] = self.smtp_user
            send_kwargs["password"] = self.smtp_password

        await aiosmtplib.send(message, **send_kwargs)
        logger.info(f"SMTP | Email sent successfully to {to_email}")

    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        headers: dict[str, str] | None = None,
    ):
        """Sends email via SendGrid HTTP API."""
        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": self.smtp_from_email, "name": "LILY Beauty Salon"},
            "subject": subject,
            "content": [{"type": "text/html", "value": html_content}],
        }
        if headers:
            payload["headers"] = headers
        headers = {
            "Authorization": f"Bearer {self.sendgrid_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.sendgrid_url, json=payload, headers=headers, timeout=10.0)
            if response.status_code not in [200, 201, 202]:
                raise Exception(f"SendGrid API error: {response.status_code} - {response.text}")

        logger.info(f"SendGrid | Email sent successfully to {to_email}")

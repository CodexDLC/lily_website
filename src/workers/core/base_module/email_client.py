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

    async def send_email(self, to_email: str, subject: str, html_content: str, timeout: int = 15):
        """
        Основной метод отправки.
        """
        try:
            # ПОПЫТКА 1: SMTP
            await self._send_via_smtp(to_email, subject, html_content, timeout)
        except Exception as e:
            logger.warning(f"SMTP failed ({e}). Switching to SendGrid API...")

            # ПОПЫТКА 2: SendGrid API (если есть ключ)
            if self.sendgrid_api_key:
                await self._send_via_api(to_email, subject, html_content, timeout)
            else:
                logger.error("SendGrid API Key is missing. Cannot fallback.")
                raise e

    async def _send_via_smtp(self, to_email: str, subject: str, html_content: str, timeout: int):
        message = EmailMessage()
        message["From"] = self.smtp_from_email
        message["To"] = to_email
        message["Subject"] = subject
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

        logger.debug(f"SMTP | Sending to {to_email} via {self.smtp_host}")
        await aiosmtplib.send(message, **send_kwargs)
        logger.info(f"SMTP | Email sent successfully to {to_email}")

    async def _send_via_api(self, to_email: str, subject: str, html_content: str, timeout: int):
        """Отправка через SendGrid HTTP API (порт 443)."""
        headers = {"Authorization": f"Bearer {self.sendgrid_api_key}", "Content-Type": "application/json"}

        payload = {
            "personalizations": [{"to": [{"email": to_email}], "subject": subject}],
            "from": {"email": self.smtp_from_email, "name": "Lily Beauty Salon"},
            "content": [{"type": "text/html", "value": html_content}],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.sendgrid_url, headers=headers, json=payload, timeout=timeout)

        if response.status_code in [200, 201, 202]:
            logger.info(f"API | Email sent successfully via SendGrid to {to_email}")
        else:
            logger.error(f"API | SendGrid Error: {response.status_code} - {response.text}")
            raise Exception(f"SendGrid API failed: {response.text}")

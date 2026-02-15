from email.message import EmailMessage
from typing import Any

import aiosmtplib
from loguru import logger


class AsyncEmailClient:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        smtp_from_email: str | None = None,
        smtp_use_tls: bool = False,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from_email = smtp_from_email
        self.smtp_use_tls = smtp_use_tls

    async def send_email(self, to_email: str, subject: str, html_content: str):
        """
        Асинхронная отправка HTML-письма.
        Поддерживает как Implicit SSL (465), так и STARTTLS (587) или обычный SMTP (1025).
        """
        message = EmailMessage()
        message["From"] = self.smtp_from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content("Please enable HTML to view this email.")
        message.add_alternative(html_content, subtype="html")

        # Авто-определение режима шифрования
        # Implicit SSL для порта 465
        use_ssl = self.smtp_port == 465
        # STARTTLS для порта 587 или если явно включено в настройках
        start_tls = self.smtp_port == 587 or (self.smtp_use_tls and self.smtp_port != 465)

        send_kwargs: dict[str, Any] = {
            "hostname": self.smtp_host,
            "port": self.smtp_port,
            "use_tls": use_ssl,
            "start_tls": start_tls,
        }

        # Добавляем аутентификацию только если переданы учетные данные
        if self.smtp_user and self.smtp_password:
            send_kwargs["username"] = self.smtp_user
            send_kwargs["password"] = self.smtp_password

        try:
            await aiosmtplib.send(message, **send_kwargs)
            logger.info(f"Email sent successfully to {to_email} via {self.smtp_host}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} via {self.smtp_host}: {e}")
            raise e

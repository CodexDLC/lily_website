from email.message import EmailMessage

import aiosmtplib
from loguru import logger


class AsyncEmailClient:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        smtp_from_email: str,
        smtp_use_tls: bool,
    ):  # smtp_use_ssl удален
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from_email = smtp_from_email
        self.smtp_use_tls = smtp_use_tls
        # self.smtp_use_ssl = smtp_use_ssl # Удалено

    async def send_email(self, to_email: str, subject: str, html_content: str):
        """
        Асинхронная отправка HTML-письма.
        """
        message = EmailMessage()
        message["From"] = self.smtp_from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content("Please enable HTML to view this email.")  # Fallback text
        message.add_alternative(html_content, subtype="html")

        try:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=self.smtp_use_tls,
                start_tls=False,  # Явно отключаем STARTTLS для прямого SSL на порту 465
                # use_ssl=self.smtp_use_ssl, # Удалено
            )
            logger.info(f"Email sent successfully to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise e

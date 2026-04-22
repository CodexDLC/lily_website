import json
import re
from typing import Any

import httpx
from loguru import logger as log
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


class TwilioService:
    """
    Сервис для отправки уведомлений через Twilio (SMS, WhatsApp).
    """

    def __init__(self, account_sid: str, auth_token: str, from_number: str, sendgrid_api_key: str | None = None):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        self.sendgrid_api_key = sendgrid_api_key
        self.sendgrid_url = "https://api.sendgrid.com/v3/mail/send"

    def _format_phone(self, phone: str) -> str:
        """Нормализация номера для Twilio (E.164)."""
        clean_phone = re.sub(r"[\s\-\(\)]", "", phone)
        if clean_phone.startswith("+"):
            return clean_phone
        if clean_phone.startswith("0"):
            return "+49" + clean_phone[1:]
        return "+" + clean_phone

    def _is_valid_media_url(self, url: str | None) -> bool:
        """Проверяет, является ли URL публичным и абсолютным."""
        if not url:
            return False
        # Twilio требует абсолютный URL, начинающийся с http/https
        # Также игнорируем локальные адреса типа 'backend' или 'localhost'
        return url.startswith("http") and "localhost" not in url and "backend" not in url

    def send_sms(self, to_number: str, message: str) -> bool:
        """Отправка обычного SMS."""
        try:
            formatted_to = self._format_phone(to_number)
            sent_message = self.client.messages.create(body=message, from_=self.from_number, to=formatted_to)
            log.info(f"TwilioService | SMS sent. SID: {sent_message.sid}")
            return True
        except TwilioRestException as e:
            log.error(f"TwilioService | SMS failed (Twilio Error): {e}")
            return False
        except Exception as e:
            log.error(f"TwilioService | SMS failed (Unexpected Error): {e}")
            return False

    def send_whatsapp_template(self, to_number: str, content_sid: str, variables: dict) -> bool:
        """
        Отправка WhatsApp через официальный Content Template.
        """
        try:
            formatted_to = self._format_phone(to_number)
            from_wa = f"whatsapp:{self.from_number}"
            to_wa = f"whatsapp:{formatted_to}"

            log.info(f"TwilioService | Sending WhatsApp Template {content_sid} to {to_wa}")

            sent_message = self.client.messages.create(
                from_=from_wa, to=to_wa, content_sid=content_sid, content_variables=json.dumps(variables)
            )
            log.info(f"TwilioService | WhatsApp Template sent. SID: {sent_message.sid}")
            return True
        except TwilioRestException as e:
            log.error(f"TwilioService | WhatsApp Template failed (Twilio Error): {e}")
            return False
        except Exception as e:
            log.error(f"TwilioService | WhatsApp Template failed (Unexpected Error): {e}")
            return False

    def send_whatsapp(self, to_number: str, message: str, media_url: str | None = None) -> bool:
        """Обычная отправка WhatsApp (Free-form)."""
        try:
            formatted_to = self._format_phone(to_number)
            from_wa = f"whatsapp:{self.from_number}"
            to_wa = f"whatsapp:{formatted_to}"

            params: dict[str, Any] = {"from_": from_wa, "to": to_wa, "body": message}

            # Используем медиа только если URL валидный
            if self._is_valid_media_url(media_url):
                params["media_url"] = [media_url]
            elif media_url:
                log.warning(f"TwilioService | Skipping invalid media URL: {media_url}")

            sent_message = self.client.messages.create(**params)
            log.info(f"TwilioService | WhatsApp sent. SID: {sent_message.sid}")
            return True
        except TwilioRestException as e:
            log.error(f"TwilioService | WhatsApp failed (Twilio Error): {e}")
            return False
        except Exception as e:
            log.error(f"TwilioService | WhatsApp failed (Unexpected Error): {e}")
            return False

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str,
        timeout: int = 15,
        headers: dict[str, str] | None = None,
    ) -> bool:
        """Отправка через SendGrid HTTP API (принадлежит Twilio)."""
        if not self.sendgrid_api_key:
            log.error("TwilioService | SendGrid API Key is missing.")
            return False

        headers = {"Authorization": f"Bearer {self.sendgrid_api_key}", "Content-Type": "application/json"}

        payload = {
            "personalizations": [{"to": [{"email": to_email}], "subject": subject}],
            "from": {"email": from_email, "name": "Lily Beauty Salon"},
            "content": [{"type": "text/html", "value": html_content}],
        }
        if headers:
            payload["headers"] = headers

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.sendgrid_url, headers=headers, json=payload, timeout=timeout)

            if response.status_code in [200, 201, 202]:
                log.info(f"TwilioService | Email sent successfully via SendGrid to {to_email}")
                return True
            else:
                log.error(f"TwilioService | SendGrid Error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            log.error(f"TwilioService | SendGrid Exception: {e}")
            return False

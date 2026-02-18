import json
import re
from typing import Any

from loguru import logger as log
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


class TwilioService:
    """
    Сервис для отправки уведомлений через Twilio (SMS, WhatsApp).
    """

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number

    def _format_phone(self, phone: str) -> str:
        """Нормализация номера для Twilio (E.164)."""
        clean_phone = re.sub(r"[\s\-\(\)]", "", phone)
        if clean_phone.startswith("+"):
            return clean_phone
        if clean_phone.startswith("0"):
            return "+49" + clean_phone[1:]
        return "+" + clean_phone

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

            # Явно указываем тип dict[str, Any], чтобы Mypy не ругался на список в media_url
            params: dict[str, Any] = {"from_": from_wa, "to": to_wa, "body": message}
            if media_url:
                params["media_url"] = [media_url]

            sent_message = self.client.messages.create(**params)
            log.info(f"TwilioService | WhatsApp sent. SID: {sent_message.sid}")
            return True
        except TwilioRestException as e:
            log.error(f"TwilioService | WhatsApp failed (Twilio Error): {e}")
            return False
        except Exception as e:
            log.error(f"TwilioService | WhatsApp failed (Unexpected Error): {e}")
            return False

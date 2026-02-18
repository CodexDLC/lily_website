import re

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
        """
        Базовая нормализация номера для Twilio (E.164).
        Если номер начинается с 0 и нет +, пытаемся привести к международному формату.
        В данном случае, если номер немецкий (01...), заменим 0 на +49.
        """
        clean_phone = re.sub(r"[\s\-\(\)]", "", phone)

        if clean_phone.startswith("+"):
            return clean_phone

        # Если номер начинается с 0, заменяем на +49 (Германия), так как салон в Кётене
        if clean_phone.startswith("0"):
            return "+49" + clean_phone[1:]

        return "+" + clean_phone

    def send_sms(self, to_number: str, message: str) -> bool:
        """
        Отправка SMS сообщения.
        """
        try:
            formatted_to = self._format_phone(to_number)
            log.info(f"TwilioService | Sending SMS to {formatted_to} (original: {to_number})")

            sent_message = self.client.messages.create(body=message, from_=self.from_number, to=formatted_to)
            log.info(f"TwilioService | SMS sent successfully. SID: {sent_message.sid}")
            return True
        except TwilioRestException as e:
            log.error(f"TwilioService | SMS failed to {to_number}: {e}")
            return False
        except Exception as e:
            log.exception(f"TwilioService | Unexpected error sending SMS to {to_number}: {e}")
            return False

    def send_whatsapp(self, to_number: str, message: str) -> bool:
        """
        Отправка WhatsApp сообщения.
        """
        try:
            formatted_to = self._format_phone(to_number)
            from_wa = f"whatsapp:{self.from_number}"
            to_wa = f"whatsapp:{formatted_to}"

            log.info(f"TwilioService | Sending WhatsApp to {to_wa}")
            sent_message = self.client.messages.create(body=message, from_=from_wa, to=to_wa)
            log.info(f"TwilioService | WhatsApp sent successfully. SID: {sent_message.sid}")
            return True
        except TwilioRestException as e:
            log.error(f"TwilioService | WhatsApp failed to {to_number}: {e}")
            return False
        except Exception as e:
            log.exception(f"TwilioService | Unexpected error sending WhatsApp to {to_number}: {e}")
            return False

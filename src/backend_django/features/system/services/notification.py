from codex_tools.notifications.adapters.django_adapter import DjangoNotificationAdapter
from codex_tools.notifications.service import BaseNotificationEngine
from core.arq.client import DjangoArqClient

from ..selectors.email_content import selector


class NotificationService(BaseNotificationEngine):
    """
    Project-specific Notification Service.
    """

    def __init__(self):
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        super().__init__(adapter=adapter)

    @classmethod
    def send_contact_receipt(
        cls, recipient_email: str, client_name: str, message_text: str, request_id: int, lang: str = "de"
    ):
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        with adapter.translation_override(lang):
            subject = selector.get_value("ct_receipt_subject", "Wir haben Ihre Anfrage erhalten")
            header_text = selector.get_value("ct_receipt_header", "Wir haben Ihre Anfrage erhalten!")
            greeting = selector.get_value("ct_receipt_greeting", "Hallo")
            body_text = selector.get_value("ct_receipt_body", "Vielen Dank für Ihre Nachricht.")
            quoted_label = selector.get_value("ct_receipt_quoted_label", "Ihre Nachricht")
            signature = selector.get_value("email_signature_common", "Mit freundlichen Grüßen\nIhr LILY Beauty Team")

        return cls().dispatch(
            recipient_email=recipient_email,
            first_name=client_name,
            template_name="ct_receipt",
            event_type="new_contact_request",
            subject=subject,
            context_data={
                "request_id": request_id,
                "client_name": client_name,
                "message_text": message_text,
                "header_text": header_text,
                "greeting": greeting,
                "body_text": body_text,
                "quoted_message_label": quoted_label,
                "signature": signature,
            },
        )

    @classmethod
    def send_admin_reply(cls, recipient_email: str, reply_text: str, history_text: str, request_id: int):
        signature = selector.get_value("email_signature_common", "Mit freundlichen Grüßen\nIhr LILY Beauty Team")

        return cls().dispatch(
            recipient_email=recipient_email,
            template_name="ct_reply",
            subject=f"Re: Your inquiry [Ref: #{request_id}]",
            context_data={
                "reply_text": reply_text,
                "history_text": history_text,
                "signature": signature,
                "request_id": request_id,
            },
            channels=["email"],
        )

    # --- Booking Notifications ---

    @classmethod
    def send_booking_confirmation(cls, recipient_email: str, client_name: str, context: dict, lang: str = "de"):
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        with adapter.translation_override(lang):
            subject = selector.get_value("bk_confirmation_subject", "Terminbestätigung")
            email_tag = selector.get_value("bk_confirmation_tag", "TERMINBESTÄTIGUNG")
            greeting = f"{selector.get_value('bk_greeting', 'Hallo')} {client_name},"
            email_body = selector.get_value("bk_confirmation_body", "Ihr Termin wurde erfolgreich bestätigt.")
            button_text = selector.get_value("bk_btn_calendar", "In den Kalender eintragen")
            signature = selector.get_value("email_signature_common", "Ihr LILY Beauty Team")

        full_context = context.copy()
        full_context.update(
            {
                "email_tag": email_tag,
                "greeting": greeting,
                "email_body": email_body,
                "email_button_text": button_text,
                "signature": signature,
            }
        )

        return cls().dispatch(
            recipient_email=recipient_email,
            first_name=client_name,
            template_name="bk_confirmation",
            subject=subject,
            context_data=full_context,
            channels=["email"],
        )

    @classmethod
    def send_booking_cancellation(cls, recipient_email: str, client_name: str, context: dict, lang: str = "de"):
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        with adapter.translation_override(lang):
            subject = selector.get_value("bk_cancellation_subject", "Terminabsage")
            email_tag = selector.get_value("bk_cancellation_tag", "TERMINABSAGE")
            greeting = f"{selector.get_value('bk_greeting', 'Hallo')} {client_name},"
            base_body = selector.get_value("bk_cancellation_body", "Ihr Termin wurde storniert.")
            email_body = f"{base_body}\n\n{context.get('reason_text', '')}"
            signature = selector.get_value("email_signature_common", "Ihr LILY Beauty Team")

        full_context = context.copy()
        full_context.update(
            {"email_tag": email_tag, "greeting": greeting, "email_body": email_body, "signature": signature}
        )

        return cls().dispatch(
            recipient_email=recipient_email,
            first_name=client_name,
            template_name="bk_cancellation",
            subject=subject,
            context_data=full_context,
            channels=["email"],
        )

    @classmethod
    def send_booking_no_show(cls, recipient_email: str, client_name: str, context: dict, lang: str = "de"):
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        with adapter.translation_override(lang):
            subject = selector.get_value("bk_noshow_subject", "Termin verpasst?")
            email_tag = selector.get_value("bk_noshow_tag", "TERMIN VERPASST")
            greeting = f"{selector.get_value('bk_greeting', 'Hallo')} {client_name},"
            email_body = selector.get_value(
                "bk_noshow_body", "Sie haben Ihren Termin verpasst. Bitte kontaktieren Sie uns."
            )
            signature = selector.get_value("email_signature_common", "Ihr LILY Beauty Team")

        full_context = context.copy()
        full_context.update(
            {"email_tag": email_tag, "greeting": greeting, "email_body": email_body, "signature": signature}
        )

        return cls().dispatch(
            recipient_email=recipient_email,
            first_name=client_name,
            template_name="bk_no_show",
            subject=subject,
            context_data=full_context,
            channels=["email"],
        )

    @classmethod
    def send_booking_reschedule(cls, recipient_email: str, client_name: str, context: dict, lang: str = "de"):
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        with adapter.translation_override(lang):
            subject = selector.get_value("bk_reschedule_subject", "Terminvorschlag")
            email_tag = selector.get_value("bk_reschedule_tag", "TERMINVORSCHLAG")
            greeting = f"{selector.get_value('bk_greeting', 'Hallo')} {client_name},"
            email_body = selector.get_value("bk_reschedule_body", "Wir haben einen neuen Terminvorschlag für Sie.")
            button_text = selector.get_value("bk_btn_confirm", "Termin bestätigen")
            signature = selector.get_value("email_signature_common", "Ihr LILY Beauty Team")

        full_context = context.copy()
        full_context.update(
            {
                "email_tag": email_tag,
                "greeting": greeting,
                "email_body": email_body,
                "email_button_text": button_text,
                "signature": signature,
            }
        )

        return cls().dispatch(
            recipient_email=recipient_email,
            first_name=client_name,
            template_name="bk_reschedule",
            subject=subject,
            context_data=full_context,
            channels=["email"],
        )

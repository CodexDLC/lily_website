from __future__ import annotations

from codex_tools.notifications.adapters.django_adapter import DjangoNotificationAdapter
from codex_tools.notifications.service import BaseNotificationEngine
from core.arq.client import DjangoArqClient
from django.core.cache import cache

from ..selectors.email_content import selector


# Event type constants
class NotificationEventType:
    BOOKING_RECEIVED = "booking_received"
    APPOINTMENT_CONFIRMED = "appointment_confirmed"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    APPOINTMENT_NO_SHOW = "appointment_no_show"
    APPOINTMENT_RESCHEDULED = "appointment_rescheduled"
    APPOINTMENT_REMINDER = "appointment_reminder"
    GROUP_BOOKING = "new_group_booking"
    CONTACT_REQUEST = "new_contact_request"


_engine: NotificationService | None = None


def _get_engine() -> NotificationService:
    global _engine
    if _engine is None:
        _engine = NotificationService()
    return _engine


_SITE_SETTINGS_ADDRESS_CACHE_KEY = "site_settings_address"
_SITE_SETTINGS_ADDRESS_CACHE_TTL = 3600


def _get_salon_address() -> str:
    addr: str | None = cache.get(_SITE_SETTINGS_ADDRESS_CACHE_KEY)
    if addr is None:
        try:
            from features.system.models.site_settings import SiteSettings  # noqa: PLC0415

            s = SiteSettings.load()
            addr = f"{s.address_street}, {s.address_postal_code} {s.address_locality}"
            cache.set(_SITE_SETTINGS_ADDRESS_CACHE_KEY, addr, timeout=_SITE_SETTINGS_ADDRESS_CACHE_TTL)
        except Exception:
            addr = ""
    return addr


# Module-level frozenset: event types that pass through to the bot wire AS-IS.
# All other booking events are normalised to 'new_appointment' for compatibility.
# TODO: Remove this constant once the Telegram bot consumer handles correct event types.
_BOT_WIRE_PASSTHROUGH_EVENTS: frozenset[str] = frozenset(
    {
        NotificationEventType.CONTACT_REQUEST,
        NotificationEventType.GROUP_BOOKING,
    }
)


class NotificationService(BaseNotificationEngine):
    """
    Project-specific Notification Service.
    All public send_* methods call _dispatch_notification.
    """

    def __init__(self) -> None:
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        super().__init__(adapter=adapter)

    @classmethod
    def _dispatch_notification(
        cls,
        *,
        recipient_email: str,
        client_name: str,
        template_name: str,
        event_type: str,
        channels: list[str],
        lang: str,
        base_context: dict,
        selector_map: dict[str, tuple[str, str]],
        override_fields: dict[str, str] | None = None,
        recipient_phone: str | None = None,
    ) -> bool:
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        fetched: dict[str, str] = {}
        with adapter.translation_override(lang):
            for ctx_key, (sel_key, fallback) in selector_map.items():
                fetched[ctx_key] = selector.get_value(sel_key, fallback)
        full_context: dict = {
            **base_context,
            **fetched,
            **(override_fields or {}),
            "salon_address": _get_salon_address(),
        }
        # TODO: Remove once Telegram bot handles correct event types.
        wire_event_type = event_type if event_type in _BOT_WIRE_PASSTHROUGH_EVENTS else "new_appointment"
        return _get_engine().dispatch(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            first_name=client_name,
            template_name=template_name,
            event_type=wire_event_type,
            subject=fetched.get("subject"),
            context_data=full_context,
            channels=channels,
        )

    @classmethod
    def send_contact_receipt(
        cls,
        recipient_email: str,
        client_name: str,
        message_text: str,
        request_id: int,
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> bool:
        selector_map = {
            "subject": ("ct_receipt_subject", "Wir haben Ihre Anfrage erhalten"),
            "header_text": ("ct_receipt_header", "Wir haben Ihre Anfrage erhalten!"),
            "greeting": ("ct_receipt_greeting", "Hallo"),
            "body_text": ("ct_receipt_body", "Vielen Dank fuer Ihre Nachricht."),
            "quoted_message_label": ("ct_receipt_quoted_label", "Ihre Nachricht"),
            "signature": ("email_signature_common", "Mit freundlichen Gruessen\nIhr LILY Beauty Team"),
        }
        return cls._dispatch_notification(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="ct_receipt",
            event_type=NotificationEventType.CONTACT_REQUEST,
            channels=["email", "telegram"],
            lang=lang,
            base_context={"request_id": request_id, "client_name": client_name, "message_text": message_text},
            selector_map=selector_map,
        )

    @classmethod
    def send_admin_reply(
        cls,
        recipient_email: str,
        reply_text: str,
        history_text: str,
        request_id: int,
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> bool:
        selector_map = {"signature": ("email_signature_common", "Mit freundlichen Gruessen\nIhr LILY Beauty Team")}
        return cls._dispatch_notification(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name="",
            template_name="ct_reply",
            event_type=NotificationEventType.CONTACT_REQUEST,
            channels=["email"],
            lang=lang,
            base_context={"reply_text": reply_text, "history_text": history_text, "request_id": request_id},
            selector_map=selector_map,
            override_fields={"subject": f"Re: Your inquiry [Ref: #{request_id}]"},
        )

    @classmethod
    def send_booking_confirmation(
        cls,
        recipient_email: str,
        client_name: str,
        context: dict,
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> bool:
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        with adapter.translation_override(lang):
            greeting_base = selector.get_value("bk_greeting", "Hallo")
        selector_map = {
            "subject": ("bk_confirmation_subject", "Terminbestaetigung"),
            "email_tag": ("bk_confirmation_tag", "TERMINBESTAETIGUNG"),
            "email_body": ("bk_confirmation_body", "Ihr Termin wurde успешно bestaetigt."),
            "email_button_text": ("bk_btn_calendar", "In den Kalender eintragen"),
            "signature": ("email_signature_common", "Ihr LILY Beauty Team"),
        }
        return cls._dispatch_notification(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="bk_confirmation",
            event_type=NotificationEventType.APPOINTMENT_CONFIRMED,
            channels=["email", "telegram"],
            lang=lang,
            base_context=context,
            selector_map=selector_map,
            override_fields={"greeting": f"{greeting_base} {client_name},"},
        )

    @classmethod
    def send_booking_cancellation(
        cls,
        recipient_email: str,
        client_name: str,
        context: dict,
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> bool:
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        with adapter.translation_override(lang):
            greeting_base = selector.get_value("bk_greeting", "Hallo")
            base_body = selector.get_value("bk_cancellation_body", "Ihr Termin wurde storniert.")
        email_body = f"{base_body}\n\n{context.get('reason_text', '')}"
        selector_map = {
            "subject": ("bk_cancellation_subject", "Terminabsage"),
            "email_tag": ("bk_cancellation_tag", "TERMINABSAGE"),
            "signature": ("email_signature_common", "Ihr LILY Beauty Team"),
        }
        return cls._dispatch_notification(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="bk_cancellation",
            event_type=NotificationEventType.APPOINTMENT_CANCELLED,
            channels=["email", "telegram"],
            lang=lang,
            base_context=context,
            selector_map=selector_map,
            override_fields={"greeting": f"{greeting_base} {client_name},", "email_body": email_body},
        )

    @classmethod
    def send_booking_no_show(
        cls,
        recipient_email: str,
        client_name: str,
        context: dict,
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> bool:
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        with adapter.translation_override(lang):
            greeting_base = selector.get_value("bk_greeting", "Hallo")
        selector_map = {
            "subject": ("bk_noshow_subject", "Termin verpasst?"),
            "email_tag": ("bk_noshow_tag", "TERMIN VERPASST"),
            "email_body": ("bk_noshow_body", "Sie haben Ihren Termin verpasst. Bitte kontaktieren Sie uns."),
            "signature": ("email_signature_common", "Ihr LILY Beauty Team"),
        }
        return cls._dispatch_notification(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="bk_no_show",
            event_type=NotificationEventType.APPOINTMENT_NO_SHOW,
            channels=["email", "telegram"],
            lang=lang,
            base_context=context,
            selector_map=selector_map,
            override_fields={"greeting": f"{greeting_base} {client_name},"},
        )

    @classmethod
    def send_booking_receipt(
        cls,
        recipient_email: str,
        client_name: str,
        context: dict,
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> bool:
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        with adapter.translation_override(lang):
            greeting_base = selector.get_value("bk_greeting", "Hallo")
        selector_map = {
            "subject": ("bk_receipt_subject", "Eingangsbestätigung: Ihre Terminanfrage"),
            "email_tag": ("bk_receipt_tag", "STATUS: IN PRÜFUNG ⏳"),
            "email_body": (
                "bk_receipt_body",
                "Wir prüfen, ob der Termin verfügbar ist. Bitte warten Sie auf die verbindliche Bestätigung.",
            ),
            "signature": ("email_signature_common", "Ihr LILY Beauty Team"),
        }
        return cls._dispatch_notification(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="bk_receipt",
            event_type=NotificationEventType.BOOKING_RECEIVED,
            channels=["email", "telegram"],
            lang=lang,
            base_context=context,
            selector_map=selector_map,
            override_fields={"greeting": f"{greeting_base} {client_name},"},
        )

    @classmethod
    def send_booking_reschedule(
        cls,
        recipient_email: str,
        client_name: str,
        context: dict,
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> bool:
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        with adapter.translation_override(lang):
            greeting_base = selector.get_value("bk_greeting", "Hallo")
        selector_map = {
            "subject": ("bk_reschedule_subject", "Terminvorschlag"),
            "email_tag": ("bk_reschedule_tag", "TERMINVORSCHLAG"),
            "email_body": ("bk_reschedule_body", "Wir haben einen neuen Terminvorschlag fuer Sie."),
            "email_button_text": ("bk_btn_confirm", "Termin bestaetigen"),
            "signature": ("email_signature_common", "Ihr LILY Beauty Team"),
        }
        return cls._dispatch_notification(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="bk_reschedule",
            event_type=NotificationEventType.APPOINTMENT_RESCHEDULED,
            channels=["email", "telegram"],
            lang=lang,
            base_context=context,
            selector_map=selector_map,
            override_fields={"greeting": f"{greeting_base} {client_name},"},
        )

    @classmethod
    def send_booking_reminder(
        cls,
        recipient_email: str,
        client_name: str,
        context: dict,
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> bool:
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        with adapter.translation_override(lang):
            greeting_base = selector.get_value("bk_greeting", "Hallo")
        selector_map = {
            "subject": ("bk_reminder_subject", "Terminerinnerung"),
            "email_tag": ("bk_reminder_tag", "ERINNERUNG"),
            "intro_text": ("bk_reminder_body", "Wir freuen uns auf Sie! Hier ist eine Erinnerung an Ihren Termin."),
            "email_button_text": ("bk_btn_reschedule", "Termin umbuchen"),
            "signature": ("email_signature_common", "Ihr LILY Beauty Team"),
        }
        # salon_address is always injected by _dispatch_notification from SiteSettings cache.
        return cls._dispatch_notification(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="bk_reminder",
            event_type=NotificationEventType.APPOINTMENT_REMINDER,
            channels=["email", "telegram"],
            lang=lang,
            base_context=context,
            selector_map=selector_map,
            override_fields={"greeting": f"{greeting_base} {client_name},"},
        )

    @classmethod
    def send_group_booking_confirmation(
        cls,
        recipient_email: str,
        client_name: str,
        context: dict,
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> bool:
        """Unified confirmation for multiple services."""
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        with adapter.translation_override(lang):
            greeting_base = selector.get_value("bk_greeting", "Hallo")
        selector_map = {
            "subject": ("bk_group_confirmation_subject", "Terminbestaetigung"),
            "email_tag": ("bk_group_confirmation_tag", "TERMINBESTAETIGUNG"),
            "email_button_text": ("bk_btn_calendar", "In den Kalender eintragen"),
            "signature": ("email_signature_common", "Ihr LILY Beauty Team"),
        }
        return cls._dispatch_notification(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="bk_group_booking",
            event_type=NotificationEventType.GROUP_BOOKING,
            channels=["email", "telegram"],
            lang=lang,
            base_context=context,
            selector_map=selector_map,
            override_fields={"greeting": f"{greeting_base} {client_name},"},
        )

    @classmethod
    def send_marketing_reengagement(
        cls,
        recipient_email: str,
        client_name: str,
        context: dict,
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> bool:
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        with adapter.translation_override(lang):
            greeting_base = selector.get_value("bk_greeting", "Hallo")
        selector_map = {
            "subject": ("mk_reengagement_subject", "Zeit fuer Dich"),
            "email_tag": ("mk_reengagement_tag", "ZEIT FUER DICH"),
            "body_text": ("mk_reengagement_body", "Wir haben Sie schon lange nicht mehr gesehen..."),
            "signature": ("email_signature_common", "Ihr LILY Beauty Team"),
        }
        return cls._dispatch_notification(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="mk_reengagement",
            event_type=NotificationEventType.CONTACT_REQUEST,
            channels=["email"],
            lang=lang,
            base_context=context,
            selector_map=selector_map,
            override_fields={"greeting": f"{greeting_base} {client_name},"},
        )

"""
Universal Notification Service for LILY Beauty Salon.

This is the single entry-point for all outbound notifications:
  - Booking lifecycle (confirmation, cancellation, reminder, reschedule, no-show)
  - Contact form receipt + admin alert
  - Admin → client replies

Architecture
------------
Uses codex_django.notifications engine with:
  - DjangoQueueAdapter (ARQ) when REDIS_URL is available
  - DjangoDirectAdapter (inline Django send_mail) as fallback
  - EmailContent model via BaseEmailContentSelector for localised subject/body text
  - @notification_handler decorator for event-driven dispatch

Usage
-----
    from features.conversations.services.notifications import NotificationService

    NotificationService.send_booking_confirmation(
        recipient_email="client@example.com",
        client_name="Anna",
        lang="de",
        context={...},
    )

    # Or via event dispatch (used by signals/tasks):
    engine.dispatch_event("booking.confirmed", appointment)
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from codex_django.notifications import (
    BaseEmailContentSelector,
    BaseNotificationEngine,
    DjangoCacheAdapter,
    DjangoDirectAdapter,
    DjangoI18nAdapter,
    DjangoQueueAdapter,
    NotificationDispatchSpec,
    notification_handler,
)
from django.conf import settings

log = logging.getLogger(__name__)

_HAS_ARQ = bool(getattr(settings, "ARQ_REDIS_URL", None) or getattr(settings, "REDIS_URL", None))


# ─────────────────────────────────────────────────────────────────────────────
# Infrastructure (singletons)
# ─────────────────────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def _get_selector() -> BaseEmailContentSelector:
    from system.models import EmailContent

    return BaseEmailContentSelector(
        model=EmailContent,
        cache_adapter=DjangoCacheAdapter() if _HAS_ARQ else None,
        i18n_adapter=DjangoI18nAdapter(),
    )


@lru_cache(maxsize=1)
def _get_engine() -> BaseNotificationEngine:
    engine_arq_client = None
    if _HAS_ARQ:
        import contextlib

        with contextlib.suppress(ImportError, ModuleNotFoundError):
            from core.arq.client import DjangoArqClient

            engine_arq_client = DjangoArqClient

    if engine_arq_client:
        queue: Any = DjangoQueueAdapter(arq_client=engine_arq_client)
    else:
        log.warning("ARQ client not found or disabled. Falling back to DjangoDirectAdapter.")
        queue = DjangoDirectAdapter()

    return BaseNotificationEngine(
        queue_adapter=queue,
        cache_adapter=DjangoCacheAdapter(),
        i18n_adapter=DjangoI18nAdapter(),
        selector=_get_selector(),
    )


def _t(key: str, lang: str, fallback: str = "") -> str:
    """Resolve a localised text block from EmailContent. Returns fallback on miss."""
    return _get_selector().get(key, lang) or fallback


def _should_notify(email: str, field: str) -> bool:
    """Check if the user with the given email has enabled the specified notification type."""
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    user = user_model.objects.filter(email=email).first()
    if user and hasattr(user, "profile"):
        return getattr(user.profile, field, True)
    return True


# ─────────────────────────────────────────────────────────────────────────────
# NotificationService  (high-level project API)
# ─────────────────────────────────────────────────────────────────────────────


class NotificationService:
    """High-level send_* methods for all project notification events."""

    # ── Booking ──────────────────────────────────────────────────────────────

    @classmethod
    def send_booking_receipt(
        cls,
        *,
        recipient_email: str,
        client_name: str,
        context: dict[str, Any],
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> str | None:
        """Send booking-received auto-receipt to client."""
        if not _should_notify(recipient_email, "notify_service"):
            return None

        greeting = _t("bk_greeting", lang, "Hallo")
        return _get_engine().dispatch(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="bk_receipt",
            event_type="booking.received",
            channels=["email", "telegram"],
            language=lang,
            subject_key="bk_receipt_subject",
            subject=_t("bk_receipt_subject", lang, "Eingangsbestätigung: Ihre Terminanfrage"),
            greeting=f"{greeting} {client_name},",
            email_tag=_t("bk_receipt_tag", lang, "STATUS: IN PRÜFUNG ⏳"),
            email_body=_t(
                "bk_receipt_body",
                lang,
                "Wir prüfen, ob der Termin verfügbar ist. Bitte warten Sie auf die verbindliche Bestätigung.",
            ),
            signature=_t("email_signature_common", lang, "Ihr LILY Beauty Team"),
            **context,
        )

    @classmethod
    def send_booking_confirmation(
        cls,
        *,
        recipient_email: str,
        client_name: str,
        context: dict[str, Any],
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> str | None:
        """Send booking confirmed email to client."""
        if not _should_notify(recipient_email, "notify_service"):
            return None

        greeting = _t("bk_greeting", lang, "Hallo")
        return _get_engine().dispatch(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="bk_confirmation",
            event_type="booking.confirmed",
            channels=["email", "telegram"],
            language=lang,
            subject_key="bk_confirmation_subject",
            subject=_t("bk_confirmation_subject", lang, "Terminbestätigung"),
            greeting=f"{greeting} {client_name},",
            email_tag=_t("bk_confirmation_tag", lang, "TERMINBESTÄTIGUNG"),
            email_body=_t("bk_confirmation_body", lang, "Ihr Termin wurde erfolgreich bestätigt."),
            email_button_text=_t("bk_btn_calendar", lang, "In den Kalender eintragen"),
            signature=_t("email_signature_common", lang, "Ihr LILY Beauty Team"),
            **context,
        )

    @classmethod
    def send_booking_cancellation(
        cls,
        *,
        recipient_email: str,
        client_name: str,
        context: dict[str, Any],
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> str | None:
        """Send booking cancelled email to client."""
        if not _should_notify(recipient_email, "notify_service"):
            return None

        greeting = _t("bk_greeting", lang, "Hallo")
        base_body = _t("bk_cancellation_body", lang, "Ihr Termin wurde storniert.")
        reason = context.pop("reason_text", "")
        body = f"{base_body}\n\n{reason}".strip() if reason else base_body
        return _get_engine().dispatch(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="bk_cancellation",
            event_type="booking.cancelled",
            channels=["email", "telegram"],
            language=lang,
            subject_key="bk_cancellation_subject",
            subject=_t("bk_cancellation_subject", lang, "Terminabsage"),
            greeting=f"{greeting} {client_name},",
            email_tag=_t("bk_cancellation_tag", lang, "TERMINABSAGE"),
            email_body=body,
            signature=_t("email_signature_common", lang, "Ihr LILY Beauty Team"),
            **context,
        )

    @classmethod
    def send_booking_reschedule(
        cls,
        *,
        recipient_email: str,
        client_name: str,
        context: dict[str, Any],
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> str | None:
        """Send rescheduled-appointment proposal to client."""
        if not _should_notify(recipient_email, "notify_service"):
            return None

        greeting = _t("bk_greeting", lang, "Hallo")
        return _get_engine().dispatch(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="bk_reschedule",
            event_type="booking.rescheduled",
            channels=["email", "telegram"],
            language=lang,
            subject_key="bk_reschedule_subject",
            subject=_t("bk_reschedule_subject", lang, "Terminvorschlag"),
            greeting=f"{greeting} {client_name},",
            email_tag=_t("bk_reschedule_tag", lang, "TERMINVORSCHLAG"),
            email_body=_t("bk_reschedule_body", lang, "Wir haben einen neuen Terminvorschlag für Sie."),
            email_button_text=_t("bk_btn_confirm", lang, "Termin bestätigen"),
            signature=_t("email_signature_common", lang, "Ihr LILY Beauty Team"),
            **context,
        )

    @classmethod
    def send_booking_reminder(
        cls,
        *,
        recipient_email: str,
        client_name: str,
        context: dict[str, Any],
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> str | None:
        """Send appointment reminder email to client."""
        if not _should_notify(recipient_email, "notify_reminders"):
            return None

        greeting = _t("bk_greeting", lang, "Hallo")
        return _get_engine().dispatch(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="bk_reminder",
            event_type="booking.reminder",
            channels=["email", "telegram"],
            language=lang,
            subject_key="bk_reminder_subject",
            subject=_t("bk_reminder_subject", lang, "Terminerinnerung"),
            greeting=f"{greeting} {client_name},",
            email_tag=_t("bk_reminder_tag", lang, "ERINNERUNG"),
            intro_text=_t(
                "bk_reminder_body", lang, "Wir freuen uns auf Sie! Hier ist eine Erinnerung an Ihren Termin."
            ),
            email_button_text=_t("bk_btn_reschedule", lang, "Termin umbuchen"),
            signature=_t("email_signature_common", lang, "Ihr LILY Beauty Team"),
            **context,
        )

    @classmethod
    def send_booking_no_show(
        cls,
        *,
        recipient_email: str,
        client_name: str,
        context: dict[str, Any],
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> str | None:
        """Send no-show follow-up to client."""
        if not _should_notify(recipient_email, "notify_service"):
            return None

        greeting = _t("bk_greeting", lang, "Hallo")
        return _get_engine().dispatch(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="bk_no_show",
            event_type="booking.no_show",
            channels=["email", "telegram"],
            language=lang,
            subject_key="bk_noshow_subject",
            subject=_t("bk_noshow_subject", lang, "Termin verpasst?"),
            greeting=f"{greeting} {client_name},",
            email_tag=_t("bk_noshow_tag", lang, "TERMIN VERPASST"),
            email_body=_t("bk_noshow_body", lang, "Sie haben Ihren Termin verpasst. Bitte kontaktieren Sie uns."),
            signature=_t("email_signature_common", lang, "Ihr LILY Beauty Team"),
            **context,
        )

    # ── Contact Form ──────────────────────────────────────────────────────────

    @classmethod
    def send_contact_receipt(
        cls,
        *,
        recipient_email: str,
        client_name: str,
        message_text: str,
        request_id: int,
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> str | None:
        """Send auto-receipt to client after contact form submission."""
        return _get_engine().dispatch(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name=client_name,
            template_name="ct_receipt",
            event_type="contact.receipt",
            channels=["email", "telegram"],
            language=lang,
            subject_key="ct_receipt_subject",
            subject=_t("ct_receipt_subject", lang, "Wir haben Ihre Anfrage erhalten | LILY Beauty"),
            header_text=_t("ct_receipt_header", lang, "Wir haben Ihre Anfrage erhalten!"),
            greeting=_t("ct_receipt_greeting", lang, "Hallo"),
            body_text=_t("ct_receipt_body", lang, "Vielen Dank für Ihre Nachricht."),
            quoted_message_label=_t("ct_receipt_quoted_label", lang, "Ihre Nachricht"),
            signature=_t("email_signature_common", lang, "Ihr LILY Beauty Team"),
            request_id=request_id,
            message_text=message_text,
        )

    # ── Account & Auth ────────────────────────────────────────────────────────

    @classmethod
    def send_account_verification(
        cls,
        *,
        recipient_email: str,
        activate_url: str,
        user_name: str = "Client",
        signup: bool = True,
        lang: str = "de",
    ) -> str | None:
        """Send email verification/confirmation link (signup or change)."""
        subject_key = "acc_verify_signup_subject" if signup else "acc_verify_email_subject"
        body_key = "acc_verify_signup_body" if signup else "acc_verify_email_body"

        fallback_subject = "Bitte bestätigen Sie Ihre E-Mail-Adresse"
        fallback_body = (
            "Vielen Dank für Ihre Registrierung. Bitte klicken Sie на ссылку ниже, чтобы подтвердить свой аккаунт."
        )

        greeting = _t("bk_greeting", lang, "Hallo")
        return _get_engine().dispatch(
            recipient_email=recipient_email,
            client_name=user_name,
            template_name="acc_verification",
            event_type="account.verification",
            channels=["email"],
            language=lang,
            subject_key=subject_key,
            subject=_t(subject_key, lang, fallback_subject),
            activate_url=activate_url,
            email_body=_t(body_key, lang, fallback_body),
            greeting=f"{greeting} {user_name},",
            signature=_t("email_signature_common", lang, "Ihr LILY Beauty Team"),
        )

    @classmethod
    def send_password_reset(
        cls,
        *,
        recipient_email: str,
        reset_url: str,
        user_name: str = "Client",
        lang: str = "de",
    ) -> str | None:
        """Send password reset link."""
        greeting = _t("bk_greeting", lang, "Hallo")
        return _get_engine().dispatch(
            recipient_email=recipient_email,
            client_name=user_name,
            template_name="acc_password_reset",
            event_type="account.password_reset",
            channels=["email"],
            language=lang,
            subject_key="pwd_reset_subject",
            subject=_t("pwd_reset_subject", lang, "Passwort zurücksetzen"),
            reset_url=reset_url,
            email_body=_t(
                "pwd_reset_body",
                lang,
                "Sie haben das Zurücksetzen Ihres Passworts angefordert. Klicken Sie auf den Link unten.",
            ),
            greeting=f"{greeting} {user_name},",
            signature=_t("email_signature_common", lang, "Ihr LILY Beauty Team"),
        )

    @classmethod
    def send_admin_reply(
        cls,
        *,
        recipient_email: str,
        reply_text: str,
        history_text: str,
        request_id: int,
        recipient_phone: str | None = None,
        lang: str = "de",
    ) -> str | None:
        """Send an admin reply back to the client."""
        return _get_engine().dispatch(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            client_name="",
            template_name="ct_reply",
            event_type="contact.reply",
            channels=["email"],
            language=lang,
            subject_key="",
            subject=f"Re: Your inquiry [Ref: #{request_id}]",
            signature=_t("email_signature_common", lang, "Ihr LILY Beauty Team"),
            reply_text=reply_text,
            history_text=history_text,
            request_id=request_id,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Event handlers (wired to notification_event_registry)
# ─────────────────────────────────────────────────────────────────────────────


@notification_handler("conversations.new_message")
def _handle_new_contact_message(message) -> list[NotificationDispatchSpec]:
    """Notify all staff (ADMINS) of a new contact form message."""
    specs = []
    for _idx, email in getattr(settings, "ADMINS", ()):
        if not email:
            continue
        subject = f"[New message] {message.sender_name} — {(message.subject or message.body)[:60]}"
        body = (
            f"From: {message.sender_name} <{message.sender_email}>\n"
            f"Topic: {message.get_topic_display()}\n"
            f"Source: {message.get_source_display()}\n\n"
            f"{message.body}"
        )
        specs.append(
            NotificationDispatchSpec(
                recipient_email=email,
                subject_key="",
                subject=subject,
                event_type="conversations.new_message",
                channels=["email"],
                mode="rendered",
                text_content=body,
            )
        )
    return specs

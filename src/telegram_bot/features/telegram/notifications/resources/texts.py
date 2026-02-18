from html import escape
from typing import cast

from aiogram_i18n import I18nContext

from src.shared.utils.text import sanitize_for_sms, transliterate


class NotificationsTexts:
    """
    Текстовые константы для фичи Notifications.
    """

    @staticmethod
    def get_i18n():
        return cast("I18nContext", I18nContext.get_current())

    # === Тексты для Telegram (динамические) ===
    @classmethod
    def title(cls):
        return cls.get_i18n().notifications.title()

    @classmethod
    def description(cls):
        return cls.get_i18n().notifications.description()

    @classmethod
    def status_approved(cls):
        return cls.get_i18n().notifications.status.approved()

    @classmethod
    def status_rejected(cls):
        return cls.get_i18n().notifications.status.rejected()

    @classmethod
    def prompt_select_reason(cls):
        return cls.get_i18n().notifications.prompt.select.reason()

    @classmethod
    def alert_approved(cls):
        return cls.get_i18n().notifications.alert.approved()

    @classmethod
    def alert_rejected(cls):
        return cls.get_i18n().notifications.alert.rejected()

    @classmethod
    def alert_cancelled(cls):
        return cls.get_i18n().notifications.alert.cancelled()

    @classmethod
    def alert_deleted(cls):
        return cls.get_i18n().notifications.alert.deleted()

    @classmethod
    def error_api(cls):
        return cls.get_i18n().notifications.error.api()

    # === Тексты для Email-уведомлений (немецкий) ===
    EMAIL_REJECT_REASON_BUSY = "Leider ist der gewünschte Termin bereits vergeben. Bitte wählen Sie eine andere Zeit."
    EMAIL_REJECT_REASON_ILL = "Leider muss der Termin aufgrund einer Erkrankung des Masters verschoben werden."
    EMAIL_REJECT_REASON_MATERIALS = "Leider fehlen derzeit die notwendigen Materialien für diese Dienstleistung."
    EMAIL_REJECT_REASON_BLACKLIST = "Leider können wir Ihre Anfrage derzeit nicht annehmen."

    @staticmethod
    def get_sms_confirm_text(first_name: str, date: str, time: str, master: str = "") -> str:
        """
        Текст для SMS/WhatsApp уведомления (немецкий).
        """
        clean_name = sanitize_for_sms(first_name, max_length=30)
        clean_name = transliterate(clean_name)

        clean_date = sanitize_for_sms(date, max_length=10)
        clean_time = sanitize_for_sms(time, max_length=5)

        return f"Hallo {clean_name}, Ihr Termin am {clean_date} um {clean_time} im Lily Beauty Salon ist bestätigt. Wir freuen uns auf Sie!"

    EMAIL_CONFIRM_TAG = "TERMINBESTÄTIGUNG"
    EMAIL_CONFIRM_SUBJECT = "Terminbestätigung - Lily Beauty Salon"
    EMAIL_CONFIRM_BODY = "Vielen Gracias für Ihre Buchung. Ihr Termin wurde erfolgreich bestätigt. Wir freuen uns darauf, Sie bei uns begrüßen zu dürfen."

    EMAIL_CANCEL_TAG = "TERMINABSAGE"
    EMAIL_CANCEL_SUBJECT = "Terminstornierung - Lily Beauty Salon"
    EMAIL_CANCEL_BODY = "Leider müssen wir Ihren Termin absagen. Wir entschuldigen uns für die Unannehmlichkeiten."

    @staticmethod
    def get_email_greeting(first_name: str, last_name: str, visits_count: int | str) -> str:
        try:
            v_count = int(visits_count)
        except (ValueError, TypeError):
            v_count = 0

        if v_count == 0:
            full_name = f"{first_name} {last_name}".strip()
            return f"Sehr geehrte/r {escape(full_name)},"
        elif 1 <= v_count <= 4:
            return f"Liebe/r {escape(first_name)},"
        else:
            return f"Hallo {escape(first_name)},"

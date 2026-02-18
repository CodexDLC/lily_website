from typing import cast

from aiogram_i18n import I18nContext


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
    def _translit(text: str) -> str:
        """Простая транслитерация для имен."""
        translit_map = str.maketrans(
            {
                "а": "a",
                "б": "b",
                "в": "v",
                "г": "g",
                "д": "d",
                "е": "e",
                "ё": "yo",
                "ж": "zh",
                "з": "z",
                "и": "i",
                "й": "y",
                "к": "k",
                "л": "l",
                "м": "m",
                "н": "n",
                "о": "o",
                "п": "p",
                "р": "r",
                "с": "s",
                "т": "t",
                "у": "u",
                "ф": "f",
                "х": "kh",
                "ц": "ts",
                "ч": "ch",
                "ш": "sh",
                "щ": "shch",
                "ъ": "",
                "ы": "y",
                "ь": "",
                "э": "e",
                "ю": "yu",
                "я": "ya",
                "А": "A",
                "Б": "B",
                "В": "V",
                "Г": "G",
                "Д": "D",
                "Е": "E",
                "Ё": "Yo",
                "Ж": "Zh",
                "З": "Z",
                "И": "I",
                "Й": "Y",
                "К": "K",
                "Л": "L",
                "М": "M",
                "Н": "N",
                "О": "O",
                "П": "P",
                "Р": "R",
                "С": "S",
                "Т": "T",
                "У": "U",
                "Ф": "F",
                "Х": "Kh",
                "Ц": "Ts",
                "Ч": "Ch",
                "Ш": "Sh",
                "Щ": "Shch",
                "Ъ": "",
                "Ы": "Y",
                "Ь": "",
                "Э": "E",
                "Ю": "Yu",
                "Я": "Ya",
            }
        )
        return text.translate(translit_map)

    @staticmethod
    def get_sms_confirm_text(first_name: str, date: str, time: str, master: str = "") -> str:
        """
        Текст для SMS/WhatsApp уведомления (немецкий).
        Убрали мастера, чтобы избежать кириллицы и путаницы.
        """
        clean_name = NotificationsTexts._translit(first_name)
        return f"Hallo {clean_name}, Ihr Termin am {date} um {time} im Lily Beauty Salon ist bestätigt. Wir freuen uns на Sie!"

    EMAIL_CONFIRM_TAG = "TERMINBESTÄTIGUNG"
    EMAIL_CONFIRM_SUBJECT = "Terminbestätigung - Lily Beauty Salon"
    EMAIL_CONFIRM_BODY = "Vielen Dank für Ihre Buchung. Ihr Termin wurde успешно bestätigt. Wir freuen uns darauf, Sie bei uns begrüßen zu dürfen."

    EMAIL_CANCEL_TAG = "TERMINABSAGE"
    EMAIL_CANCEL_SUBJECT = "Terminstornierung - Lily Beauty Salon"
    EMAIL_CANCEL_BODY = "Leider müssen wir Ihren Termin absagen. Wir entschuldigen uns für die Unannehmmlichkeiten."

    @staticmethod
    def get_email_greeting(first_name: str, last_name: str, visits_count: int | str) -> str:
        try:
            v_count = int(visits_count)
        except (ValueError, TypeError):
            v_count = 0

        if v_count == 0:
            full_name = f"{first_name} {last_name}".strip()
            return f"Sehr geehrte/r {full_name},"
        elif 1 <= v_count <= 4:
            return f"Liebe/r {first_name},"
        else:
            return f"Hallo {first_name},"

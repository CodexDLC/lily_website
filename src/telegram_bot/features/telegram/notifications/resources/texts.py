class NotificationsTexts:
    """
    Текстовые константы для фичи Notifications.
    """

    TITLE = "👋 <b>Notifications</b>"
    DESCRIPTION = "Это стартовый экран фичи Notifications."
    BUTTON_ACTION = "Нажми меня"
    BUTTON_BACK = "🔙 Назад"

    # === Причины отклонения (для кнопок Telegram) ===
    REJECT_REASON_BUSY = "Мастер занят / Нет времени"
    REJECT_REASON_ILL = "Мастер заболел"
    REJECT_REASON_MATERIALS = "Нет материалов для услуги"
    REJECT_REASON_BLACKLIST = "Клиент в черном списке"
    BUTTON_CANCEL_REJECT = "🔙 Отмена"

    # === Пост-действия ===
    BUTTON_DELETE = "🗑 Удалить из ленты"
    ALERT_DELETED = "Сообщение удалено"

    # === Тексты для Email-уведомлений (на немецком) ===
    EMAIL_REJECT_REASON_BUSY = "Leider ist der gewünschte Termin bereits vergeben. Bitte wählen Sie eine andere Zeit."
    EMAIL_REJECT_REASON_ILL = "Leider muss der Termin aufgrund einer Erkrankung des Masters verschoben werden."
    EMAIL_REJECT_REASON_MATERIALS = "Leider fehlen derzeit die notwendigen Materialien für diese Dienstleistung."
    EMAIL_REJECT_REASON_BLACKLIST = "Leider können wir Ihre Anfrage derzeit nicht annehmen."

    # === Статусы ===
    STATUS_APPROVED = "✅ ЗАЯВКА ПОДТВЕРЖДЕНА"
    STATUS_REJECTED = "❌ ЗАЯВКА ОТКЛОНЕНА"

    # === Промпты ===
    PROMPT_SELECT_REASON = "Выберите причину отклонения:"

    # === Alerts ===
    ALERT_APPROVED = "Заявка подтверждена, письмо отправлено"
    ALERT_REJECTED = "Заявка отклонена"
    ALERT_CANCELLED = "Отменено"
    ERROR_API = "⚠️ Ошибка связи с сервером"

    # === Email Content (DE) ===
    EMAIL_CONFIRM_TAG = "TERMINBESTÄTIGUNG"
    EMAIL_CONFIRM_SUBJECT = "Terminbestätigung - Lily Beauty Salon"
    EMAIL_CONFIRM_BODY = "Vielen Dank für Ihre Buchung. Ihr Termin wurde erfolgreich bestätigt. Wir freuen uns darauf, Sie bei uns begrüßen zu dürfen."

    EMAIL_CANCEL_TAG = "TERMINABSAGE"
    EMAIL_CANCEL_SUBJECT = "Terminstornierung - Lily Beauty Salon"
    EMAIL_CANCEL_BODY = "Leider müssen wir Ihren Termin absagen. Wir entschuldigen uns für die Unannehmlichkeiten."

    @staticmethod
    def get_email_greeting(first_name: str, last_name: str, visits_count: int | str) -> str:
        """Формирует грамматически верное приветствие на немецком."""
        try:
            v_count = int(visits_count)
        except (ValueError, TypeError):
            v_count = 0

        if v_count == 0:
            # Новый клиент - формально (Имя + Фамилия)
            full_name = f"{first_name} {last_name}".strip()
            return f"Sehr geehrte/r {full_name},"
        elif 1 <= v_count <= 4:
            # Постоянный клиент - менее формально (только Имя)
            return f"Liebe/r {first_name},"
        else:
            # VIP/Друг - дружелюбно (только Имя)
            return f"Hallo {first_name},"

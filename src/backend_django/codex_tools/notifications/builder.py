"""
codex_tools.notifications.builder
==================================
Стандартизация данных для уведомлений.

Отвечает за создание унифицированного словаря (payload), который
понимает Notification Worker. Гарантирует наличие всех необходимых
полей: ID уведомления, данные получателя, каналы связи и контекст.
"""

import uuid


class NotificationPayloadBuilder:
    """
    Построитель универсального пакета данных для уведомлений.

    Используется на стороне Django для подготовки задачи в очередь.
    """

    @staticmethod
    def build(
        recipient_email: str | None = None,
        recipient_phone: str | None = None,
        first_name: str = "Guest",
        last_name: str = "",
        template_name: str | None = None,
        event_type: str | None = None,
        subject: str | None = None,
        context_data: dict | None = None,
        channels: list[str] | None = None,
        notification_id: str | None = None,
    ) -> dict:
        """
        Создает валидный словарь для задачи send_universal_notification_task.

        Args:
            recipient_email: Email получателя (для канала email).
            recipient_phone: Телефон получателя (для канала sms/whatsapp).
            first_name: Имя получателя для приветствия.
            last_name: Фамилия получателя.
            template_name: Короткое имя шаблона (например, 'ct_receipt').
            event_type: Тип события для Telegram-бота (например, 'new_request').
            subject: Тема письма (опционально).
            context_data: Словарь данных для рендеринга шаблона.
            channels: Список активных каналов ['email', 'telegram', 'sms'].
            notification_id: Уникальный UUID для трекинга (генерируется если пуст).

        Returns:
            dict: Стандартизированный payload.
        """
        return {
            "notification_id": notification_id or str(uuid.uuid4()),
            "recipient": {
                "email": recipient_email,
                "phone": recipient_phone,
                "first_name": first_name,
                "last_name": last_name,
            },
            "template_name": template_name,
            "event_type": event_type,
            "subject": subject,
            "context_data": context_data or {},
            "channels": channels or ["email", "telegram"],
        }

from typing import Any

from .texts import NotificationsTexts


class NotificationsFormatter:
    """
    Форматирование сообщений для фичи Notifications.
    """

    def format_main(self, payload: Any) -> str:
        """
        Формирует текст главного экрана.
        """
        # Пример использования payload
        user_name = payload.get("name", "User") if isinstance(payload, dict) else "User"

        return f"{NotificationsTexts.TITLE}\n\n{NotificationsTexts.DESCRIPTION}\nUser: {user_name}"

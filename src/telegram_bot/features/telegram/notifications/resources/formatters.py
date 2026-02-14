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

        return f"{NotificationsTexts.TITLE}\n\n{NotificationsTexts.DESCRIPTION}\nUser: "

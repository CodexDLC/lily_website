from typing import Any

from .texts import DjangoListenerTexts


class DjangoListenerFormatter:
    """
    Форматирование сообщений для фичи DjangoListener.
    """

    def format_main(self, payload: Any) -> str:
        """
        Формирует текст главного экрана.
        """
        # Пример использования payload
        user_name = payload.get("name", "User") if isinstance(payload, dict) else "User"

        return f"{DjangoListenerTexts.TITLE}\n\n{DjangoListenerTexts.DESCRIPTION}\nUser: {user_name}"

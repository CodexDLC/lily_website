from typing import Any

from src.telegram_bot.features.notifications.resources.formatters import NotificationsFormatter
from src.telegram_bot.features.notifications.resources.keyboards import build_main_kb
from src.telegram_bot.services.base.view_dto import ViewResultDTO


class NotificationsUI:
    """
    UI сервис для фичи Notifications.
    Использует форматтеры и клавиатуры из ресурсов.
    """

    def __init__(self):
        self.formatter = NotificationsFormatter()

    def render_main(self, payload: Any) -> ViewResultDTO:
        text = self.formatter.format_main(payload)
        kb = build_main_kb()

        return ViewResultDTO(text=text, kb=kb)

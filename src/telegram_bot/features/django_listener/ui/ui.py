from typing import Any

from src.telegram_bot.features.django_listener.resources.formatters import DjangoListenerFormatter
from src.telegram_bot.features.django_listener.resources.keyboards import build_main_kb
from src.telegram_bot.services.base.view_dto import ViewResultDTO


class DjangoListenerUI:
    """
    UI сервис для фичи DjangoListener.
    Использует форматтеры и клавиатуры из ресурсов.
    """

    def __init__(self):
        self.formatter = DjangoListenerFormatter()

    def render_main(self, payload: Any) -> ViewResultDTO:
        text = self.formatter.format_main(payload)
        kb = build_main_kb()

        return ViewResultDTO(text=text, kb=kb)

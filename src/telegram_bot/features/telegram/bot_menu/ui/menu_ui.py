"""
UI для фичи bot_menu.
"""

from src.telegram_bot.features.telegram.bot_menu.resources.keyboards import build_dashboard_keyboard
from src.telegram_bot.features.telegram.bot_menu.resources.texts import get_dashboard_title
from src.telegram_bot.services.base.view_dto import ViewResultDTO


class BotMenuUI:
    """
    Отвечает за рендеринг главного меню (Дашборда).
    """

    def render_dashboard(self, buttons: dict, mode: str = "bot_menu") -> ViewResultDTO:
        """
        Генерирует ViewResultDTO.
        Мы выводим заголовок, а затем перечисляем доступные фичи с их описанием.
        """
        title = get_dashboard_title(mode)

        # Сортируем кнопки для списка (так же, как в клавиатуре)
        sorted_buttons = sorted(buttons.values(), key=lambda x: x.get("priority", 100))

        description_lines = []
        for btn in sorted_buttons:
            icon = btn.get("icon", "")
            label = btn.get("text", "Feature")
            desc = btn.get("description", "")

            line = f"{icon} <b>{label}</b>"
            if desc:
                line += f" — {desc}"
            description_lines.append(line)

        full_text = title
        if description_lines:
            full_text += "\n\nДоступные функции:\n" + "\n".join(description_lines)

        return ViewResultDTO(text=full_text, kb=build_dashboard_keyboard(buttons, mode))

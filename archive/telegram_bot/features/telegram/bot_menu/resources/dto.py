from codex_bot.base import BaseBotContext


class MenuContext(BaseBotContext):
    """
    Контекст специфичный для фичи bot_menu.
    """

    action: str
    target: str | None = None

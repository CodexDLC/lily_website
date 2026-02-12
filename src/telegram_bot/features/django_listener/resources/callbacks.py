from aiogram.filters.callback_data import CallbackData


class DjangoListenerCallback(CallbackData, prefix="django_listener"):
    """
    CallbackData для фичи DjangoListener.
    action: действие (main, detail, etc.)
    id: опциональный идентификатор
    """

    action: str
    id: int | None = None

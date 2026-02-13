from aiogram.filters.callback_data import CallbackData


class NotificationsCallback(CallbackData, prefix="notifications"):
    """
    CallbackData для фичи Notifications.
    action: действие (approve, reject, etc.)
    id: идентификатор брони (или сессии)
    """

    action: str
    id: int | str | None = None

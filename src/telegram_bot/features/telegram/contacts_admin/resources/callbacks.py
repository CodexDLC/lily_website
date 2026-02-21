from aiogram.filters.callback_data import CallbackData


class ContactsAdminCallback(CallbackData, prefix="contacts_admin"):
    """
    Колбэк для фичи ContactsAdmin.
    """

    action: str
    target: str | None = None  # Например, category_id

    # Действия:
    # 'category' -> Просмотр 10 последних непрочитанных для этой категории
    # 'back' -> Вернуться в дашборд
    # 'refresh' -> Обновить дашборд (Summary)
    # 'item_detail' -> Детальный просмотр заявки
    # 'process' -> Отметить как обработанную

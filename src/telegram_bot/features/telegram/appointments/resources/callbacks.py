from aiogram.filters.callback_data import CallbackData


class AppointmentsCallback(CallbackData, prefix="appts"):
    """
    Колбэк для фичи Appointments.

    Действия:
    - hub       → главный экран фичи (Hub)
    - dashboard → дашборд по категориям
    - category  → список записей в категории (target=slug, page=N)
    - prev      → предыдущая страница (target=slug, page=N)
    - next      → следующая страница (target=slug, page=N)
    - back      → назад (из hub → главное меню)
    - soon      → заглушка для кнопок "скоро"
    - noop      → пустое действие (кнопка текущей страницы пагинации)
    """

    action: str
    target: str | None = None  # category_slug
    page: int = 1

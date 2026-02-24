from src.shared.utils.table_formatter import TableFormatter

from .dto import AppointmentItemDto, CategorySummaryDto

STATUS_ICON: dict[str, str] = {
    "pending": "⏳",
    "confirmed": "✅",
    "completed": "✅",
    "cancelled": "❌",
    "no_show": "🚫",
}


class AppointmentsFormatter:
    """
    Форматирование текстовых блоков для фичи Appointments.
    Использует TableFormatter для ASCII-таблиц внутри <pre>.
    """

    def format_hub(self) -> str:
        return (
            "📋 <b>Записи</b>\n\n"
            "Управление записями клиентов.\n\n"
            "📅 <b>Записи</b> — список по категориям\n"
            "🔔 <b>Напоминания</b> — скоро"
        )

    def format_dashboard(self, summaries: list[CategorySummaryDto]) -> str:
        if not summaries:
            return "📋 <b>Записи</b>\n\nЗаписей пока нет."

        legend = "📊 всего  ⏳ ожидает  ✅ подтверждено\n\n"
        headers = ["Категория", "📊", "⏳", "✅"]
        rows = [[s.category_title, s.total, s.pending, s.completed] for s in summaries]
        table = TableFormatter.format_table(headers, rows)
        return legend + f"<pre>{table}</pre>"

    def format_category_list(
        self,
        category_title: str,
        items: list[AppointmentItemDto],
        page: int,
        pages: int,
        total: int,
    ) -> str:
        pending = sum(1 for i in items if i.status == "pending")
        header = f"📋 <b>{category_title}</b> — {pending} ожидают  (стр. {page}/{pages})\n\n"

        if not items:
            return header + "Записей не найдено."

        headers = ["#", "Клиент", "Ст."]
        rows = [[idx + 1, i.client_name, STATUS_ICON.get(i.status, "?")] for idx, i in enumerate(items)]
        table = TableFormatter.format_table(headers, rows)
        return header + f"<pre>{table}</pre>"

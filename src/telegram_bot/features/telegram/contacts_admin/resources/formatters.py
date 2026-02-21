from src.shared.utils.table_formatter import TableFormatter

from .dto import ContactDetailDto, ContactPreviewDto, ContactSummaryDto
from .texts import ContactsAdminTexts


class ContactsAdminFormatter:
    """
    Форматирует данные контактов для вывода в Telegram.
    """

    @staticmethod
    def format_dashboard(summaries: list[ContactSummaryDto]) -> str:
        """Форматирует таблицу сводки."""
        headers = [
            ContactsAdminTexts.table_header_category(),
            ContactsAdminTexts.table_header_total(),
            ContactsAdminTexts.table_header_new(),
        ]
        rows = []
        for s in summaries:
            rows.append([s.category_name, s.total_count, s.unread_count])

        table_ascii = TableFormatter.format_table(headers, rows)
        table_html = f"<pre>{table_ascii}</pre>"

        title = ContactsAdminTexts.dashboard_title()
        description = ContactsAdminTexts.description()

        return f"{title}\n{description}\n\n{table_html}"

    @staticmethod
    def format_preview_list(category_name: str, unread_count: int, previews: list[ContactPreviewDto]) -> str:
        """Форматирует список заголовков (имя и тема) для быстрого ознакомления."""
        title = ContactsAdminTexts.preview_list_title(category=category_name)
        stats = ContactsAdminTexts.preview_list_stats(count=unread_count)

        lines = [title, stats, ""]

        for i, p in enumerate(previews, 1):
            name = p.first_name if p.first_name else "Guest"
            # Только заголовок/имя для быстрого сканирования
            lines.append(f"{i}. 👤 <b>{name}</b>")

        if not previews:
            lines.append("<i>(Заявок пока нет)</i>")

        return "\n".join(lines)

    @staticmethod
    def format_item_detail(item: ContactDetailDto) -> str:
        """Форматирует детальный вид заявки."""
        title = ContactsAdminTexts.item_detail_title(name=item.first_name)

        lines = [
            title,
            f"📅 <b>Дата:</b> {item.created_at[:10]}",
            f"👤 <b>Имя:</b> {item.first_name}",
        ]

        if item.phone:
            lines.append(f"📞 <b>Телефон:</b> <code>{item.phone}</code>")

        lines.append(f"\n💬 <b>Сообщение:</b>\n{item.message}")

        return "\n".join(lines)

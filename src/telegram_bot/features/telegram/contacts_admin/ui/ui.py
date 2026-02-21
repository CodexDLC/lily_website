from src.telegram_bot.services.base.view_dto import ViewResultDTO

from ..resources.dto import ContactPreviewDto, ContactSummaryDto
from ..resources.formatters import ContactsAdminFormatter
from ..resources.keyboards import (
    build_dashboard_kb,
    build_preview_list_kb,
)


class ContactsAdminUI:
    """
    UI сервис для фичи ContactsAdmin.
    """

    def __init__(self):
        self.formatter = ContactsAdminFormatter()

    def render_dashboard(self, summaries: list[ContactSummaryDto]) -> ViewResultDTO:
        text = self.formatter.format_dashboard(summaries)
        kb = build_dashboard_kb(summaries)
        return ViewResultDTO(text=text, kb=kb)

    def render_preview_list(
        self,
        category_name: str,
        unread_count: int,
        previews: list[ContactPreviewDto],
        category_id: str,
        tma_url_new: str,
        tma_url_archive: str,
    ) -> ViewResultDTO:
        text = self.formatter.format_preview_list(category_name, unread_count, previews)
        kb = build_preview_list_kb(previews, category_id, tma_url_new, tma_url_archive)
        return ViewResultDTO(text=text, kb=kb)

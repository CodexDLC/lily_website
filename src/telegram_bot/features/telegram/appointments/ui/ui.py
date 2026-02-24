from src.telegram_bot.services.base.view_dto import ViewResultDTO

from ..resources.dto import AppointmentItemDto, CategorySummaryDto
from ..resources.formatters import AppointmentsFormatter
from ..resources.keyboards import build_category_kb, build_dashboard_kb, build_hub_kb


class AppointmentsUI:
    """
    UI сервис для фичи Appointments.
    Собирает ViewResultDTO из текста (Formatter) + клавиатуры (keyboards).
    """

    def __init__(self):
        self.formatter = AppointmentsFormatter()

    def render_hub(self) -> ViewResultDTO:
        text = self.formatter.format_hub()
        kb = build_hub_kb()
        return ViewResultDTO(text=text, kb=kb)

    def render_dashboard(self, summaries: list[CategorySummaryDto]) -> ViewResultDTO:
        text = self.formatter.format_dashboard(summaries)
        kb = build_dashboard_kb(summaries)
        return ViewResultDTO(text=text, kb=kb)

    def render_category(
        self,
        category_title: str,
        items: list[AppointmentItemDto],
        page: int,
        pages: int,
        total: int,
        slug: str,
        tma_url: str,
        tma_url_new: str,
    ) -> ViewResultDTO:
        text = self.formatter.format_category_list(category_title, items, page, pages, total)
        kb = build_category_kb(slug, page, pages, tma_url, tma_url_new)
        return ViewResultDTO(text=text, kb=kb)

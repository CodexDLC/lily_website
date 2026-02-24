from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callbacks import AppointmentsCallback
from .dto import CategorySummaryDto


def build_hub_kb() -> InlineKeyboardMarkup:
    """
    Клавиатура Hub-экрана: Записи / Скоро.
    Кнопки «Назад» нет — Hub является точкой входа в фичу,
    главное меню всегда остаётся отдельным сообщением сверху.
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📅 Записи",
        callback_data=AppointmentsCallback(action="dashboard").pack(),
    )
    builder.button(
        text="🔔 Скоро",
        callback_data=AppointmentsCallback(action="soon").pack(),
    )
    builder.adjust(2)
    return builder.as_markup()


def build_dashboard_kb(summaries: list[CategorySummaryDto]) -> InlineKeyboardMarkup:
    """
    Клавиатура Dashboard: кнопки категорий (2 в ряд) + Назад.
    """
    builder = InlineKeyboardBuilder()
    for s in summaries:
        builder.button(
            text=f"{s.category_title} ({s.pending}⏳)",
            callback_data=AppointmentsCallback(action="category", target=s.category_slug).pack(),
        )
    builder.button(
        text="🔙 Назад",
        callback_data=AppointmentsCallback(action="hub").pack(),
    )

    # По 2 кнопки в ряд для категорий, последняя (Назад) — одна
    n = len(summaries)
    row_sizes = [2] * (n // 2)
    if n % 2:
        row_sizes.append(1)
    row_sizes.append(1)  # Назад
    builder.adjust(*row_sizes)
    return builder.as_markup()


def build_category_kb(
    slug: str,
    page: int,
    pages: int,
    tma_url: str,
    tma_url_new: str,
) -> InlineKeyboardMarkup:
    """
    Клавиатура списка по категории: пагинация + TMA кнопки + Назад.
    """
    builder = InlineKeyboardBuilder()

    # Пагинация: ◀ | N/M | ▶
    builder.row(
        InlineKeyboardButton(
            text="◀",
            callback_data=AppointmentsCallback(action="prev", target=slug, page=max(1, page - 1)).pack(),
        ),
        InlineKeyboardButton(
            text=f"{page}/{pages}",
            callback_data=AppointmentsCallback(action="noop", target=slug, page=page).pack(),
        ),
        InlineKeyboardButton(
            text="▶",
            callback_data=AppointmentsCallback(action="next", target=slug, page=min(pages, page + 1)).pack(),
        ),
    )

    # TMA кнопки
    builder.row(
        InlineKeyboardButton(text="📋 Просмотр записей", web_app=WebAppInfo(url=tma_url)),
        InlineKeyboardButton(text="➕ Новая запись", web_app=WebAppInfo(url=tma_url_new)),
    )

    # Назад
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=AppointmentsCallback(action="dashboard").pack(),
        )
    )

    return builder.as_markup()

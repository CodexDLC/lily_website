from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callbacks import ContactsAdminCallback
from .dto import ContactPreviewDto, ContactSummaryDto
from .texts import ContactsAdminTexts


def build_dashboard_kb(summaries: list[ContactSummaryDto]) -> InlineKeyboardMarkup:
    """
    Клавиатура главного экрана: кнопки категорий + Обновить.
    """
    builder = InlineKeyboardBuilder()

    # Кнопки категорий
    for s in summaries:
        builder.button(
            text=f"📂 {s.category_name} ({s.unread_count})",
            callback_data=ContactsAdminCallback(action="category", target=s.category_id).pack(),
        )

    # Кнопка обновления
    builder.button(text=ContactsAdminTexts.btn_refresh(), callback_data=ContactsAdminCallback(action="refresh").pack())

    builder.adjust(1)  # Все кнопки в один столбец для чистоты
    return builder.as_markup()


def build_preview_list_kb(
    previews: list[ContactPreviewDto], category_id: str, tma_url_new: str, tma_url_archive: str
) -> InlineKeyboardMarkup:
    """
    Клавиатура подменю категории: список заявок + системные кнопки.
    """
    builder = InlineKeyboardBuilder()

    # 1. Кнопки открытия TMA (Уровень 3)
    builder.row(
        InlineKeyboardButton(text="📥 Необработанные (TMA)", web_app=WebAppInfo(url=tma_url_new)),
        InlineKeyboardButton(text="🎞 Архив (TMA)", web_app=WebAppInfo(url=tma_url_archive)),
    )

    # 2. Навигация в боте
    builder.row(
        InlineKeyboardButton(
            text=ContactsAdminTexts.btn_back(), callback_data=ContactsAdminCallback(action="back").pack()
        ),
        InlineKeyboardButton(
            text=ContactsAdminTexts.btn_refresh(), callback_data=ContactsAdminCallback(action="refresh").pack()
        ),
    )

    return builder.as_markup()

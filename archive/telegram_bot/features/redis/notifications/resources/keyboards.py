from typing import cast

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext

from .callbacks import NotificationsCallback


def build_main_kb(
    booking_id: int | str, topic_id: int | None = None, base_url: str = "https://lily-salon.de"
) -> InlineKeyboardMarkup:
    """
    Основная клавиатура (Ссылка на CRM).
    """
    i18n = cast("I18nContext", I18nContext.get_current())
    builder = InlineKeyboardBuilder()

    # Формируем чистую ссылку на записи в CRM
    crm_url = f"{base_url.rstrip('/')}/ru/cabinet/crm/appointments/"

    builder.button(
        text=i18n.notifications.btn.open.crm(),
        url=crm_url,
    )

    return builder.as_markup()


def build_post_action_kb(booking_id: int | str, topic_id: int | None = None) -> InlineKeyboardMarkup:
    """
    Клавиатура после действия (только кнопка Удалить).
    """
    i18n = cast("I18nContext", I18nContext.get_current())
    builder = InlineKeyboardBuilder()

    builder.button(
        text=i18n.notifications.btn.delete(),
        callback_data=NotificationsCallback(
            action="delete_notification", session_id=booking_id, topic_id=topic_id
        ).pack(),
    )

    return builder.as_markup()


def build_contact_preview_kb(
    request_id: int | str, bot_username: str = "", topic_id: int | None = None
) -> InlineKeyboardMarkup:
    """
    Клавиатура превью контактной заявки в канале-алертов (Открыть бота + Удалить).
    """
    i18n = cast("I18nContext", I18nContext.get_current())
    builder = InlineKeyboardBuilder()

    url = f"https://t.me/{bot_username}" if bot_username else "https://t.me/"

    builder.button(text=i18n.notifications.btn.open.bot(), url=url)
    builder.button(
        text=i18n.notifications.btn.delete(),
        callback_data=NotificationsCallback(
            action="delete_notification", session_id=f"contact_{request_id}", topic_id=None
        ).pack(),
    )

    builder.adjust(1)
    return builder.as_markup()

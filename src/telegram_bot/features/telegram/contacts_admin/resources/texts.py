from typing import cast

from aiogram_i18n import I18nContext


class ContactsAdminTexts:
    """
    Текстовые ресурсы для фичи контактов с поддержкой i18n.
    """

    @staticmethod
    def dashboard_title() -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.dashboard.title()

    @staticmethod
    def description() -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.description()

    @staticmethod
    def table_header_category() -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.table.category()

    @staticmethod
    def table_header_total() -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.table.total()

    @staticmethod
    def table_header_new() -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.table.new()

    @staticmethod
    def preview_list_title(category: str) -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.preview.list.title(category=category)

    @staticmethod
    def preview_list_stats(count: int) -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.preview.list.stats(count=count)

    @staticmethod
    def btn_back() -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.btn.back()

    @staticmethod
    def btn_refresh() -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.btn.refresh()

    @staticmethod
    def btn_archive() -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.btn.archive()

    @staticmethod
    def btn_open_tma() -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.btn.open_tma()

    @staticmethod
    def btn_contact_preview(name: str, preview: str) -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.btn.contact.preview(name=name, preview=preview)

    @staticmethod
    def item_detail_title(name: str) -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.item.detail.title(name=name)

    @staticmethod
    def btn_process() -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.btn.process()

    @staticmethod
    def process_success() -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.process.success()

    @staticmethod
    def process_error() -> str:
        i18n = cast("I18nContext", I18nContext.get_current())
        return i18n.admin.contacts.process.error()

from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callbacks import NotificationsCallback


def build_main_kb(appointment_id: int, topic_id: int | None = None):
    """
    Клавиатура управления заявкой (Подтвердить / Отклонить).
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Подтвердить",
        callback_data=NotificationsCallback(action="approve", session_id=appointment_id, topic_id=topic_id).pack(),
    )
    builder.button(
        text="❌ Отклонить",
        callback_data=NotificationsCallback(action="reject", session_id=appointment_id, topic_id=topic_id).pack(),
    )

    builder.adjust(2)
    return builder.as_markup()


def build_reject_reasons_kb(appointment_id: int, topic_id: int | None = None):
    """
    Клавиатура с причинами отклонения.
    """
    from .texts import NotificationsTexts

    builder = InlineKeyboardBuilder()

    reasons = [
        ("reject_busy", NotificationsTexts.REJECT_REASON_BUSY),
        ("reject_ill", NotificationsTexts.REJECT_REASON_ILL),
        ("reject_materials", NotificationsTexts.REJECT_REASON_MATERIALS),
        ("reject_blacklist", NotificationsTexts.REJECT_REASON_BLACKLIST),
    ]

    for action, text in reasons:
        builder.button(
            text=text,
            callback_data=NotificationsCallback(action=action, session_id=appointment_id, topic_id=topic_id).pack(),
        )

    builder.button(
        text=NotificationsTexts.BUTTON_CANCEL_REJECT,
        callback_data=NotificationsCallback(
            action="cancel_reject", session_id=appointment_id, topic_id=topic_id
        ).pack(),
    )

    builder.adjust(1)
    return builder.as_markup()


def build_post_action_kb(appointment_id: int, topic_id: int | None = None):
    """
    Клавиатура после обработки (кнопка удаления).
    """
    from .texts import NotificationsTexts

    builder = InlineKeyboardBuilder()
    builder.button(
        text=NotificationsTexts.BUTTON_DELETE,
        callback_data=NotificationsCallback(
            action="delete_notification", session_id=appointment_id, topic_id=topic_id
        ).pack(),
    )
    return builder.as_markup()

from typing import cast

from aiogram_i18n import I18nContext

from .dto import BookingNotificationPayload


def format_new_booking(
    payload: BookingNotificationPayload,
    email_status: str = "none",
    twilio_status: str = "none",
    email_label: str = "",
    twilio_label: str = "",
) -> str:
    """
    Формирует текст уведомления о новой брони с учетом статусов отправки.
    """
    i18n = cast("I18nContext", I18nContext.get_current())

    title = i18n.notifications.new.booking.title(client_name=payload.client_name)

    if payload.visits_count == 0:
        visits_info = i18n.notifications.new.booking.visits.new()
    else:
        visits_info = i18n.notifications.new.booking.visits.regular(count=payload.visits_count + 1)

    client_notes = payload.client_notes if payload.client_notes else "—"
    price_str = f"{payload.price:g}"

    promo_info = ""
    if payload.active_promo_title:
        promo_info = i18n.notifications.new.booking.promo(title=payload.active_promo_title)

    details = i18n.notifications.new.booking.details(
        id=payload.id,
        client_name=payload.client_name,
        client_phone=payload.client_phone,
        visits_info=visits_info,
        service_name=payload.service_name,
        datetime=payload.datetime,
        master_name=payload.master_name,
        price=price_str,
        client_notes=client_notes,
        promo_info=promo_info,
    )

    # Добавляем блок статусов, если они не "none"
    status_block = ""
    if email_status != "none" or twilio_status != "none":
        icons = i18n.notifications.status.icons
        e_icon = getattr(icons, email_status, lambda: "❓")()
        t_icon = getattr(icons, twilio_status, lambda: "❓")()

        effective_email_label = email_label or payload.email_notification_label or ""
        effective_twilio_label = twilio_label or payload.twilio_notification_label or ""

        status_block = "\n" + i18n.notifications.status.block(
            email_status=e_icon,
            email_label=effective_email_label,
            twilio_status=t_icon,
            twilio_label=effective_twilio_label,
        )

    return f"{title}\n\n{details}{status_block}"


def format_contact_preview() -> str:
    """
    Формирует короткий текст превью контактной заявки.
    """
    i18n = cast("I18nContext", I18nContext.get_current())
    return i18n.notifications.new.contact.preview.text()

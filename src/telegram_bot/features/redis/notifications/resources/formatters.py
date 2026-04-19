from .dto import BookingNotificationPayload
from .texts import NotificationsTexts


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
    title = NotificationsTexts.NEW_BOOKING_TITLE.format(client_name=payload.client_name)

    if payload.visits_count == 0:
        visits_info = "Новый клиент 🆕"
    else:
        visits_info = f"Постоянный клиент ({payload.visits_count + 1}-й визит) ⭐"

    client_notes = payload.client_notes if payload.client_notes else "—"
    price_str = f"{payload.price:g}"

    promo_info = ""
    if payload.active_promo_title:
        promo_info = f"🎯 <b>Промо:</b> {payload.active_promo_title}\n"

    details = NotificationsTexts.BOOKING_DETAILS.format(
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
        e_icon = NotificationsTexts.STATUS_ICONS.get(email_status, "❓")
        t_icon = NotificationsTexts.STATUS_ICONS.get(twilio_status, "❓")
        effective_email_label = email_label or payload.email_notification_label or ""
        effective_twilio_label = twilio_label or payload.twilio_notification_label or ""
        status_block = "\n" + NotificationsTexts.NOTIFICATION_STATUSES.format(
            email_status=e_icon,
            email_label=effective_email_label,
            twilio_status=t_icon,
            twilio_label=effective_twilio_label,
        )

    return f"{title}\n\n{details}{status_block}"


def format_contact_preview() -> str:
    """
    Формирует короткий текст превью контактной заявки.
    Полный текст — из Redis-кеша при нажатии «Прочитать».
    """
    return NotificationsTexts.CONTACT_PREVIEW_TEXT

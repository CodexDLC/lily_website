from .dto import BookingNotificationPayload
from .texts import NotificationsTexts


def format_new_booking(payload: BookingNotificationPayload) -> str:
    """
    Формирует текст уведомления о новой брони.
    """
    title = NotificationsTexts.NEW_BOOKING_TITLE.format(client_name=payload.client_name)

    if payload.visits_count == 0:
        visits_info = "Новый клиент 🆕"
    else:
        visits_info = f"Постоянный клиент ({payload.visits_count + 1}-й визит) ⭐"

    client_notes = payload.client_notes if payload.client_notes else "—"
    price_str = f"{payload.price:g}"

    # Format promo info
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

    return f"{title}\n\n{details}"

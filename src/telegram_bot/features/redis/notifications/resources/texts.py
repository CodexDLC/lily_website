class NotificationsTexts:
    """
    Текстовые шаблоны для уведомлений.
    """

    NEW_BOOKING_TITLE = "✨ <b>Новая запись: {client_name}</b>"

    BOOKING_DETAILS = (
        "📅 <b>Когда:</b> {datetime}\n"
        "✂️ <b>Услуга:</b> {service_name}\n"
        "👤 <b>Мастер:</b> {master_name}\n"
        "────────────────────\n"
        "📊 <b>Визиты:</b> {visits_info}\n"
        "💰 <b>Сумма:</b> {price} €\n"
        "{promo_info}"
        "📝 <b>Заметка:</b> {client_notes}\n\n"
        "🆔 <b>ID записи:</b> #{id}"
    )

    # Статусы уведомлений клиенту
    NOTIFICATION_STATUSES = "────────────────────\n📧 <b>Email:</b> {email_status}\n📱 <b>WhatsApp:</b> {twilio_status}"

    STATUS_ICONS = {"waiting": "⏳", "sent": "✅", "success": "✅", "failed": "❌", "none": "—"}

    BTN_APPROVE = "✅ Подтвердить"
    BTN_REJECT = "❌ Отклонить"

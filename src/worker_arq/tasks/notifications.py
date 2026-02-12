from typing import Any

from loguru import logger as log


async def send_notification_task(ctx: dict, user_id: int, message: str) -> None:
    """
    Задача отправки уведомления пользователю.
    """
    log.info(f"Task | send_notification user_id={user_id} message='{message}'")

    # Получаем бота из контекста (он должен быть добавлен в bot_worker.py)
    bot = ctx.get("bot")
    if bot:
        try:
            await bot.send_message(chat_id=user_id, text=message)
            log.info("Task | send_notification status=sent")
        except Exception as e:
            log.error(f"Task | send_notification status=failed error={e}")
    else:
        log.error("Task | send_notification status=failed error='Bot instance not found in context'")


async def send_booking_notification_task(ctx: dict, admin_id: int, appointment_data: dict[str, Any]) -> None:
    """
    Задача отправки уведомления администратору о новом бронировании.

    Args:
        ctx: Контекст ARQ (содержит bot instance)
        admin_id: Telegram ID администратора из settings.TELEGRAM_ADMIN_ID
        appointment_data: Словарь с данными о записи
            {
                'id': int,
                'client_name': str,
                'client_phone': str,
                'client_email': str,
                'service_name': str,
                'master_name': str,
                'datetime': str,  # форматированная дата
                'price': float,
                'request_call': bool,
            }
    """
    log.info(f"Task | send_booking_notification appointment_id={appointment_data.get('id')}")

    # Получаем бота из контекста
    bot = ctx.get("bot")
    if not bot:
        log.error("Task | send_booking_notification status=failed error='Bot instance not found'")
        return

    # Форматируем сообщение
    message = (
        "🔔 <b>Новая запись!</b>\n\n"
        f"👤 Клиент: {appointment_data['client_name']}\n"
        f"📱 Телефон: {appointment_data['client_phone']}\n"
        f"📧 Email: {appointment_data['client_email']}\n"
        f"💅 Услуга: {appointment_data['service_name']}\n"
        f"👩‍🦰 Мастер: {appointment_data['master_name']}\n"
        f"📅 Дата: {appointment_data['datetime']}\n"
        f"💰 Цена: {appointment_data['price']}€\n"
    )

    if appointment_data.get("request_call"):
        message += "\n⚠️ <b>Клиент просит перезвонить!</b>"

    # Отправляем сообщение (активировано для тестирования)
    try:
        await bot.send_message(chat_id=admin_id, text=message, parse_mode="HTML")
        log.info(f"Task | send_booking_notification status=sent appointment_id={appointment_data['id']}")
    except Exception as e:
        log.error(f"Task | send_booking_notification status=failed appointment_id={appointment_data['id']} error={e}")

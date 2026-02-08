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
            log.info(f"Task | send_notification status=sent")
        except Exception as e:
            log.error(f"Task | send_notification status=failed error={e}")
    else:
        log.error("Task | send_notification status=failed error='Bot instance not found in context'")

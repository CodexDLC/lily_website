from typing import Any

from aiogram import Bot
from loguru import logger as log

from src.telegram_bot.services.redis_dispatcher import bot_redis_dispatcher  # Импортируем глобальный экземпляр


@bot_redis_dispatcher.on_message("new_appointment_notification")
async def handle_new_appointment_notification(message_data: dict[str, Any], bot: Bot):
    """
    Заглушка хендлера для нового уведомления о записи.
    """
    log.info(f"Redis Stream Handler (DjangoListener): Received new appointment notification: {message_data}")
    # Здесь будет логика отправки сообщения в Telegram
    pass


# Добавьте другие хендлеры Redis Stream здесь

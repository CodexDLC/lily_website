from typing import Any

from django.conf import settings
from loguru import logger as log
from ninja import Router, Schema

from src.shared.redis_streams.stream_processor import RedisStreamProcessor  # Исправленный импорт для локального запуска

router = Router()


class StreamMessageSchema(Schema):
    message_type: str
    payload: dict[str, Any]


@router.post("/publish-stream-message/", summary="Publish a message to Redis Stream")
async def publish_stream_message(request, message: StreamMessageSchema):
    """
    Публикует сообщение в Redis Stream.
    """
    try:
        # Инициализируем RedisStreamProcessor с настройками Django
        # Для Django нам не нужен consumer_group_name и consumer_name, если он только публикует
        # Но для консистентности используем те же переменные окружения
        stream_publisher = RedisStreamProcessor(
            redis_url=settings.REDIS_URL,
            stream_name=settings.REDIS_STREAM_NAME,
            consumer_group_name=settings.REDIS_CONSUMER_GROUP_NAME,  # Используем для консистентности
            consumer_name=settings.REDIS_CONSUMER_NAME,  # Используем для консистентности
        )
        # Подключаемся к Redis
        await stream_publisher.connect()

        # Публикуем сообщение
        message_id = await stream_publisher.publish_message(message.message_type, message.payload)
        # Закрываем соединение после публикации
        await stream_publisher.stop_listening()  # stop_listening также закрывает клиент

        log.info(f"Message '{message.message_type}' published to Redis Stream with ID: {message_id}")
        return {"status": "success", "message_id": message_id}
    except Exception as e:
        log.error(f"Error publishing message to Redis Stream: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}, 500

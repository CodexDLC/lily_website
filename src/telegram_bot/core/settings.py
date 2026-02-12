"""
Конфигурация подключаемых фич и middleware.
Аналог Django INSTALLED_APPS — бот при запуске читает эти списки
и автоматически подключает роуты и middleware.
"""

import os

# Список фич для автоподключения.
# Каждая строка — путь к пакету фичи относительно telegram_bot/.
# Пакет должен содержать handlers/__init__.py с экспортом `router`.
INSTALLED_FEATURES: list[str] = [
    "features.commands",
    "features.bot_menu",
    "features.errors",
    "features.django_listener",
]

# Список middleware в порядке регистрации.
# Порядок важен: первый в списке оборачивает все последующие.
MIDDLEWARE_CLASSES: list[str] = [
    "middlewares.user_validation.UserValidationMiddleware",
    "middlewares.throttling.ThrottlingMiddleware",
    "middlewares.security.SecurityMiddleware",
    "middlewares.container.ContainerMiddleware",
]

# Настройки Redis Streams
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_STREAM_NAME: str = os.getenv("REDIS_STREAM_NAME", "bot_events")
REDIS_CONSUMER_GROUP_NAME: str = os.getenv("REDIS_CONSUMER_GROUP_NAME", "bot_group")
REDIS_CONSUMER_NAME: str = os.getenv("REDIS_CONSUMER_NAME", "bot_instance_1")

# Настройки для отправки уведомлений в Telegram канал
_channel_id_str = os.getenv("TELEGRAM_NOTIFICATION_CHANNEL_ID")
TELEGRAM_NOTIFICATION_CHANNEL_ID: int | None = int(_channel_id_str) if _channel_id_str else None

_topic_id_str = os.getenv("TELEGRAM_NOTIFICATION_TOPIC_ID")
TELEGRAM_NOTIFICATION_TOPIC_ID: int | None = int(_topic_id_str) if _topic_id_str else None

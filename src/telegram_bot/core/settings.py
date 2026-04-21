"""
Конфигурация подключаемых фич и middleware.
"""

# Фичи с интерфейсом (Aiogram роутеры)
INSTALLED_FEATURES: list[str] = [
    "features.telegram.commands",
    "features.telegram.bot_menu",
]

# Фичи-слушатели (Redis Stream)
INSTALLED_REDIS_FEATURES: list[str] = [
    "features.redis.notifications",
    "features.redis.errors",
]

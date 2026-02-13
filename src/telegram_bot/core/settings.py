"""
Конфигурация подключаемых фич и middleware.
"""

# Фичи с интерфейсом (Aiogram роутеры)
INSTALLED_FEATURES: list[str] = [
    "features.telegram.commands",
    "features.telegram.bot_menu",
    "features.telegram.notifications",
]

# Фичи-слушатели (Redis Stream)
INSTALLED_REDIS_FEATURES: list[str] = [
    "features.redis.notifications",
    "features.redis.errors",
]

# Список middleware
MIDDLEWARE_CLASSES: list[str] = [
    "middlewares.user_validation.UserValidationMiddleware",
    "middlewares.throttling.ThrottlingMiddleware",
    "middlewares.security.SecurityMiddleware",
    "middlewares.container.ContainerMiddleware",
]

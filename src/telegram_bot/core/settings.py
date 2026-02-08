"""
Конфигурация подключаемых фич и middleware.
Аналог Django INSTALLED_APPS — бот при запуске читает эти списки
и автоматически подключает роуты и middleware.
"""

# Список фич для автоподключения.
# Каждая строка — путь к пакету фичи относительно telegram_bot/.
# Пакет должен содержать handlers/__init__.py с экспортом `router`.
INSTALLED_FEATURES: list[str] = [
    "features.commands",
    "features.bot_menu",
    "features.errors",
]

# Список middleware в порядке регистрации.
# Порядок важен: первый в списке оборачивает все последующие.
MIDDLEWARE_CLASSES: list[str] = [
    "middlewares.user_validation.UserValidationMiddleware",
    "middlewares.throttling.ThrottlingMiddleware",
    "middlewares.security.SecurityMiddleware",
    "middlewares.container.ContainerMiddleware",
]

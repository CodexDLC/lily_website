# Если это ПАРНАЯ фича (обработка кнопок из Redis-уведомлений):
# 1. Импортируйте базовый колбэк:
from src.telegram_bot.features.redis.notifications.resources.callbacks import NotificationsCallback as BaseCallback

# 2. Наследуйтесь БЕЗ указания нового префикса (чтобы поймать те же события):
# class NotificationsCallback(BaseCallback):
#     pass


# Если это САМОСТОЯТЕЛЬНАЯ фича:
class NotificationsCallback(BaseCallback):
    """
    Используем тот же класс, что и в Redis-фиче.
    Ничего не добавляем, чтобы префикс и поля совпали 1-в-1.
    """

    pass

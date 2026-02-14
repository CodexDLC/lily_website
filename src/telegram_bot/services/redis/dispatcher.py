from collections.abc import Callable
from typing import Any

from aiogram import Bot
from loguru import logger as log

from .router import RedisRouter


class BotRedisDispatcher:
    """
    Диспетчер для сообщений из Redis Stream, работающий по принципу aiogram.
    Позволяет регистрировать хендлеры с помощью декораторов и подключать роутеры.
    """

    def __init__(self, bot: Bot | None = None):
        self._bot = bot
        self._container = None  # Ссылка на BotContainer
        # Словарь для хранения зарегистрированных хендлеров:
        # {message_type: [(handler_func, filter_func), ...]}
        # Хендлер принимает (payload, container)
        self._handlers: dict[
            str, list[tuple[Callable[[dict[str, Any], Any], Any], Callable[[dict[str, Any]], bool] | None]]
        ] = {}
        log.info("BotRedisDispatcher initialized.")

    def set_bot(self, bot: Bot):
        """Устанавливает объект Bot после инициализации."""
        self._bot = bot
        log.debug("Bot object set in BotRedisDispatcher.")

    def set_container(self, container):
        """Устанавливает DI контейнер."""
        self._container = container
        log.debug("Container set in BotRedisDispatcher.")

    def include_router(self, router: RedisRouter):
        """
        Подключает роутер к диспетчеру.
        Копирует все хендлеры из роутера в диспетчер.
        """
        for message_type, handlers in router.handlers.items():
            if message_type not in self._handlers:
                self._handlers[message_type] = []

            # Добавляем хендлеры из роутера
            self._handlers[message_type].extend(handlers)

        log.info(f"Included router with handlers for types: {list(router.handlers.keys())}")

    def on_message(self, message_type: str, filter_func: Callable[[dict[str, Any]], bool] | None = None):
        """
        Декоратор для регистрации хендлеров сообщений из Redis Stream.
        Хендлер должен принимать (payload, container).
        """

        def decorator(handler: Callable[[dict[str, Any], Any], Any]):
            if message_type not in self._handlers:
                self._handlers[message_type] = []
            self._handlers[message_type].append((handler, filter_func))
            log.debug(f"Registered handler for message_type='{message_type}' (handler: {handler.__name__})")
            return handler

        return decorator

    async def process_message(self, message_data: dict[str, Any]):
        """
        Обрабатывает входящее сообщение из Redis Stream, маршрутизируя его к соответствующим хендлерам.
        """
        if not self._bot:
            log.error("Bot object is not set in BotRedisDispatcher. Cannot process messages.")
            return

        if not self._container:
            log.error("Container is not set in BotRedisDispatcher. Cannot process messages.")
            return

        msg_type = message_data.get("type")
        if not msg_type:
            log.warning(f"Received Redis Stream message without 'type' field. Skipping: {message_data}")
            return

        handlers_for_type = self._handlers.get(msg_type, [])
        if not handlers_for_type:
            log.debug(f"No handlers registered for message_type='{msg_type}'. Skipping: {message_data}")
            return

        processed_any = False
        for handler, filter_func in handlers_for_type:
            try:
                if filter_func is None or filter_func(message_data):
                    log.debug(f"Calling handler {handler.__name__} for message_type='{msg_type}'")
                    # Передаем payload и container (без bot)
                    await handler(message_data, self._container)
                    processed_any = True
            except Exception as e:
                log.error(
                    f"Error in Redis Stream handler {handler.__name__} for message_type='{msg_type}': {e}",
                    exc_info=True,
                )

        if not processed_any:
            log.debug(f"No handlers matched filters for message_type='{msg_type}'. Message: {message_data}")


# Глобальный экземпляр диспетчера
bot_redis_dispatcher = BotRedisDispatcher()

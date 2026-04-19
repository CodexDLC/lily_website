from aiogram import BaseMiddleware
from codex_bot.engine.middlewares import ContainerMiddleware

from src.telegram_bot.core.container import BotContainer


def setup(container: BotContainer) -> BaseMiddleware:
    return ContainerMiddleware(container=container)

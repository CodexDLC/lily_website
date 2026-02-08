"""Installer plugins — по одному на каждый фреймворк/модуль."""

from .base import BaseInstaller
from .fastapi_installer import FastAPIInstaller
from .django_installer import DjangoInstaller
from .bot_installer import BotInstaller
from .shared_installer import SharedInstaller

__all__ = [
    "BaseInstaller",
    "FastAPIInstaller",
    "DjangoInstaller",
    "BotInstaller",
    "SharedInstaller",
]

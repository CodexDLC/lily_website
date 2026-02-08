"""
Handlers для фичи commands.
Принимает сигнал от Telegram → создаёт orchestrator → получает DTO → отдаёт sender.
"""

import contextlib

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger as log

from src.telegram_bot.core.container import BotContainer
from src.telegram_bot.features.commands.resources.texts import HELP_TEXT, SETTINGS_WIP
from src.telegram_bot.features.commands.resources.formatters import MessageInfoFormatter
from src.telegram_bot.features.commands.resources.callbacks import SettingsCallback
from src.telegram_bot.services.sender.view_sender import ViewSender

router = Router(name="commands_router")


@router.message(Command("start"))
async def cmd_start(m: Message, state: FSMContext, bot: Bot, container: BotContainer) -> None:
    """Обрабатывает команду /start."""
    if not m.from_user:
        return

    user_id = m.from_user.id

    # 1. Snapshot старых данных
    old_state_data = await state.get_data()

    # 2. Полный сброс FSM
    await state.clear()

    # Удаляем команду /start
    with contextlib.suppress(TelegramAPIError):
        await m.delete()

    # 3. Orchestrator (singleton из container) → UI
    orchestrator = container.features["commands"]
    view_dto = await orchestrator.handle_entry(user_id, payload=m.from_user)

    # 4. Sender → Telegram
    sender = ViewSender(bot, state, old_state_data, user_id)
    await sender.send(view_dto)


@router.callback_query(SettingsCallback.filter())
async def handle_settings_callback(call: CallbackQuery) -> None:
    """Обрабатывает нажатие Inline-кнопки настроек."""
    await call.answer(SETTINGS_WIP, show_alert=True)


@router.message(Command("help"))
async def cmd_help(m: Message) -> None:
    """Обрабатывает команду /help."""
    if not m.from_user:
        return
    with contextlib.suppress(TelegramAPIError):
        await m.delete()
    await m.answer(HELP_TEXT)


@router.message(Command("get_ids"))
async def cmd_get_ids(m: Message) -> None:
    """Debug: ID пользователя и чата."""
    if not m.from_user:
        return
    log.debug(f"DebugCommand | command=get_ids user_id={m.from_user.id}")
    formatted = MessageInfoFormatter.format_chat_ids(m)
    await m.answer(formatted)

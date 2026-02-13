from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.telegram_bot.core.container import BotContainer

router = Router(name="commands_router")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, container: BotContainer):
    """Обработка команды /start."""
    if not message.from_user:
        return

    orchestrator = container.features.get("commands")
    if not orchestrator:
        return

    # Вызываем логику входа
    view_dto = await orchestrator.handle_entry(message.from_user.id, payload=message.from_user)

    # Отправляем через централизованный сендер
    if container.view_sender:
        await container.view_sender.send(view_dto)


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, container: BotContainer):
    """Обработка команды /menu."""
    if not message.from_user:
        return

    # Перенаправляем на оркестратор меню
    orchestrator = container.features.get("bot_menu")
    if not orchestrator:
        return

    view_dto = await orchestrator.handle_entry(message.from_user.id)

    if container.view_sender:
        await container.view_sender.send(view_dto)

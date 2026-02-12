from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.telegram_bot.core.container import BotContainer
from src.telegram_bot.features.bot_menu.resources.callbacks import DashboardCallback
from src.telegram_bot.services.sender.view_sender import ViewSender

router = Router(name="bot_menu_router")


@router.message(Command("menu"))
async def cmd_menu(m: Message, state: FSMContext, container: BotContainer) -> None:
    """
    Принудительный вызов меню командой /menu.
    """
    if not m.from_user or not m.bot:
        return

    orchestrator = container.bot_menu

    # Передаем user_id для фильтрации кнопок
    view_dto = await orchestrator.render_menu(m.from_user.id)

    # state_data больше не передается в ViewSender, так как он извлекается внутри send()
    sender = ViewSender(m.bot, state, m.from_user.id)
    await sender.send(view_dto)


@router.callback_query(DashboardCallback.filter(F.action == "nav"))
async def on_menu_nav(
    call: CallbackQuery, callback_data: DashboardCallback, state: FSMContext, container: BotContainer
) -> None:
    """
    Обработка навигации из меню.
    """
    await call.answer()

    if not call.bot:
        return

    orchestrator = container.bot_menu

    if not callback_data.target:
        return

    # Передаем user_id для проверки прав
    view_dto = await orchestrator.handle_menu_click(callback_data.target, call.from_user.id)

    if view_dto:
        # state_data больше не передается в ViewSender, так как он извлекается внутри send()
        sender = ViewSender(call.bot, state, call.from_user.id)
        await sender.send(view_dto)

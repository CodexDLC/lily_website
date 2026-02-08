from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.telegram_bot.core.container import BotContainer
from src.telegram_bot.features.bot_menu.resources.callbacks import DashboardCallback
from src.telegram_bot.services.sender.view_sender import ViewSender

router = Router(name="bot_menu_router")


@router.message(Command("menu"))
async def cmd_menu(m: Message, state: FSMContext, container: BotContainer):
    """
    Принудительный вызов меню командой /menu.
    """
    if not m.from_user:
        return
        
    orchestrator = container.bot_menu
    
    # Передаем user_id для фильтрации кнопок
    view_dto = await orchestrator.render_menu(m.from_user.id)
    
    state_data = await state.get_data()
    sender = ViewSender(m.bot, state, state_data, m.from_user.id)
    await sender.send(view_dto)


@router.callback_query(DashboardCallback.filter(F.action == "nav"))
async def on_menu_nav(
    call: CallbackQuery, 
    callback_data: DashboardCallback, 
    state: FSMContext,
    container: BotContainer
):
    """
    Обработка навигации из меню.
    """
    await call.answer()
    
    orchestrator = container.bot_menu
    
    # Передаем user_id для проверки прав
    view_dto = await orchestrator.handle_menu_click(callback_data.target, call.from_user.id)
    
    if view_dto:
        state_data = await state.get_data()
        sender = ViewSender(call.bot, state, state_data, call.from_user.id)
        await sender.send(view_dto)

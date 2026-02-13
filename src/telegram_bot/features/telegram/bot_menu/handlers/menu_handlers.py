from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.telegram_bot.core.container import BotContainer
from src.telegram_bot.features.telegram.bot_menu.resources.callbacks import DashboardCallback

router = Router(name="bot_menu_router")


@router.callback_query(DashboardCallback.filter(F.action == "open"))
async def handle_menu_open(
    call: CallbackQuery, callback_data: DashboardCallback, state: FSMContext, container: BotContainer
):
    """Обработка открытия меню."""
    await call.answer()

    orchestrator = container.features.get("bot_menu")
    if not orchestrator:
        return

    view_dto = await orchestrator.handle_entry(call.from_user.id)

    if container.view_sender:
        await container.view_sender.send(view_dto)


@router.callback_query(DashboardCallback.filter(F.action == "select"))
async def handle_menu_select(
    call: CallbackQuery, callback_data: DashboardCallback, state: FSMContext, container: BotContainer
):
    """Обработка выбора пункта меню."""
    await call.answer()

    orchestrator = container.features.get("bot_menu")
    if not orchestrator:
        return

    # В DashboardCallback поле называется target, а не key
    view_dto = await orchestrator.handle_menu_click(callback_data.target or "", user_id=call.from_user.id)

    if container.view_sender:
        await container.view_sender.send(view_dto)

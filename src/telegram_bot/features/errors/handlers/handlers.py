from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.telegram_bot.core.container import BotContainer
from src.telegram_bot.features.errors.feature_setting import ErrorStates
from src.telegram_bot.services.director.director import Director
from src.telegram_bot.services.sender.view_sender import ViewSender

router = Router(name="errors_router")


@router.callback_query(F.data == "refresh", StateFilter(ErrorStates.main))
async def handle_refresh(call: CallbackQuery, state: FSMContext, container: BotContainer) -> None:
    """
    Обратка кнопки "Обновить" на экране ошибки.
    Пытается перезагрузить текущую ошибку (или можно сделать редирект в меню).
    """
    await call.answer("Обновление...")

    if not call.bot:
        return

    # Просто перерисовываем экран (можно добавить логику повтора операции)
    orchestrator = container.features["errors"]
    director = Director(container, state, call.from_user.id)
    orchestrator.set_director(director)

    # Получаем текущий код ошибки из стейта (если бы мы его хранили)
    # Пока просто рендерим дефолт
    view_dto = await orchestrator.render("default")

    state_data = await state.get_data()
    sender = ViewSender(call.bot, state, state_data, call.from_user.id)
    await sender.send(view_dto)


@router.callback_query(F.data == "back", StateFilter(ErrorStates.main))
async def handle_back(call: CallbackQuery, state: FSMContext, container: BotContainer) -> None:
    """
    Кнопка "Назад" - ведет в меню (или предыдущий экран, если бы была история).
    """
    await call.answer()

    # Редирект в главное меню
    director = Director(container, state, call.from_user.id)
    await director.set_scene("bot_menu", None)

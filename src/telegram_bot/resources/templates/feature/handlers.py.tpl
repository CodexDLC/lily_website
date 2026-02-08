from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter

from src.telegram_bot.core.container import BotContainer
from src.telegram_bot.services.director.director import Director
from src.telegram_bot.services.sender.view_sender import ViewSender
from src.telegram_bot.features.{feature_key}.feature_setting import {class_name}States
from src.telegram_bot.features.{feature_key}.resources.callbacks import {class_name}Callback

# TODO: Раскомментировать, если нужна анимация
# from src.telegram_bot.services.animation.animation_service import UIAnimationService

router = Router(name="{feature_key}_router")

@router.callback_query(
    {class_name}Callback.filter(F.action == "action"),
    StateFilter({class_name}States.main)
)
async def handle_action(
    call: CallbackQuery,
    callback_data: {class_name}Callback,
    state,
    container: BotContainer
):
    await call.answer()

    # 1. Получаем готовый оркестратор из контейнера
    orchestrator = container.features["{feature_key}"]

    # 2. Инициализируем Директора
    director = Director(container, state, call.from_user.id)
    orchestrator.set_director(director)

    # 3. Вызываем бизнес-логику
    view_dto = await orchestrator.handle_action(callback_data)

    # 4. Отправляем ответ
    state_data = await state.get_data()
    sender = ViewSender(call.bot, state, state_data, call.from_user.id)
    await sender.send(view_dto)


# -----------------------------------------------------------------------------
# TODO: Пример сложного хендлера с Анимацией (Polling)
# -----------------------------------------------------------------------------
# @router.callback_query(
#     {class_name}Callback.filter(F.action == "submit"),
#     StateFilter({class_name}States.main)
# )
# async def handle_submit_with_animation(
#     call: CallbackQuery,
#     callback_data: {class_name}Callback,
#     state,
#     container: BotContainer
# ):
#     """
#     Пример обработки действия с длительным ожиданием (анимация загрузки).
#     """
#     await call.answer()
#
#     orchestrator = container.features["{feature_key}"]
#     director = Director(container, state, call.from_user.id)
#     orchestrator.set_director(director)
#
#     state_data = await state.get_data()
#     sender = ViewSender(call.bot, state, state_data, call.from_user.id)
#
#     # 1. Получаем функцию-поллер из оркестратора (должна возвращать ViewDTO или None)
#     # poller = orchestrator.get_submit_poller(callback_data)
#
#     # 2. Запускаем анимацию
#     # anim_service = UIAnimationService(sender)
#     # await anim_service.run_polling_loop(
#     #     check_func=poller,
#     #     timeout=60.0,
#     #     step_interval=2.0,
#     #     loading_text="⏳ <b>Обработка...</b>"
#     # )

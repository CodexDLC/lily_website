from aiogram import Router
from aiogram.types import CallbackQuery

from src.telegram_bot.core.container import BotContainer
from src.telegram_bot.services.director.director import Director

from ..resources.callbacks import NotificationsCallback

router = Router(name="notifications_ui_router")


@router.callback_query(NotificationsCallback.filter())
async def handle_action_approve(
    call: CallbackQuery, callback_data: NotificationsCallback, state, container: BotContainer
):
    await call.answer()

    # 1. Получаем готовый оркестратор из контейнера
    orchestrator = container.features.get("notifications")
    if not orchestrator:
        return

    # 2. Инициализируем Директора
    director = Director(container, state, call.from_user.id)
    orchestrator.set_director(director)

    # 3. Вызываем бизнес-логику
    view_dto = await orchestrator.handle_action(callback_data, call)

    # 4. Отправляем ответ
    if container.view_sender:
        await container.view_sender.send(view_dto)

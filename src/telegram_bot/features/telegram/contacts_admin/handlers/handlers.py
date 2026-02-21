from aiogram import Router
from aiogram.types import CallbackQuery

from src.telegram_bot.core.container import BotContainer
from src.telegram_bot.features.telegram.contacts_admin.resources.callbacks import ContactsAdminCallback
from src.telegram_bot.services.director.director import Director

router = Router(name="contacts_admin_router")


@router.callback_query(ContactsAdminCallback.filter())
async def handle_action(call: CallbackQuery, callback_data: ContactsAdminCallback, state, container: BotContainer):
    await call.answer()

    # 1. Получаем готовый оркестратор из контейнера
    orchestrator = container.features["contacts_admin"]

    # 2. Инициализируем Директора
    director = Director(
        container=container,
        state=state,
        user_id=call.from_user.id,
        chat_id=call.message.chat.id if call.message else None,
        trigger_id=call.message.message_id if call.message else None,
    )
    orchestrator.set_director(director)

    # 3. Вызываем бизнес-логику
    view_dto = await orchestrator.handle_action(callback_data)

    # 4. Отправляем ответ
    if view_dto and container.view_sender:
        await container.view_sender.send(view_dto)

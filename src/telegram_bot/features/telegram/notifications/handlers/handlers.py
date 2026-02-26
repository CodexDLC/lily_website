from aiogram import Router
from aiogram.types import CallbackQuery
from loguru import logger

from src.telegram_bot.core.container import BotContainer
from src.telegram_bot.services.director.director import Director

from ..resources.callbacks import NotificationsCallback

router = Router(name="notifications_ui_router")


@router.callback_query(NotificationsCallback.filter())
async def handle_action_approve(
    call: CallbackQuery, callback_data: NotificationsCallback, state, container: BotContainer
):
    """
    Unified handler for all notification callback actions.
    """
    user_id = call.from_user.id
    logger.info(
        f"Bot: Notifications | Action: Callback | user_id={user_id} | action={callback_data.action} | session_id={callback_data.session_id}"
    )

    await call.answer()

    orchestrator = container.features.get("notifications")
    if not orchestrator:
        logger.error("Bot: Notifications | Action: Callback | error=OrchestratorNotFound")
        return

    try:
        # Initialize Director
        director = Director(container, state, user_id)
        orchestrator.set_director(director)

        # Call business logic
        view_dto = await orchestrator.handle_action(callback_data, call)

        # Send response via ViewSender
        if container.view_sender:
            await container.view_sender.send(view_dto)
            logger.debug(f"Bot: Notifications | Action: CallbackSuccess | user_id={user_id}")
    except Exception as e:
        logger.error(f"Bot: Notifications | Action: CallbackFailed | user_id={user_id} | error={e}")

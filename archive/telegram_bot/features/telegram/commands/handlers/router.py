from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from codex_bot.director import Director
from loguru import logger

from src.telegram_bot.core.container import BotContainer

router = Router(name="commands_router")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, container: BotContainer):
    """Handle /start command."""
    if not message.from_user:
        return

    user_id = message.from_user.id
    logger.info(f"Bot: Commands | Action: StartCommand | user_id={user_id} | username={message.from_user.username}")

    orchestrator = container.features.get("commands")
    if not orchestrator:
        logger.error("Bot: Commands | Action: StartCommand | error=OrchestratorNotFound")
        return

    try:
        director = Director(
            container=container,
            state=state,
            session_key=user_id,
            context_id=message.chat.id,
            trigger_id=message.message_id,
        )
        view_dto = await orchestrator.handle_entry(director=director, payload=message.from_user)

        if container.view_sender:
            await container.view_sender.send(view_dto)
            logger.debug(f"Bot: Commands | Action: StartCommandSuccess | user_id={user_id}")
    except Exception as e:
        logger.error(f"Bot: Commands | Action: StartCommandFailed | user_id={user_id} | error={e}")


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, container: BotContainer):
    """Handle /menu command."""
    if not message.from_user:
        return

    user_id = message.from_user.id
    logger.info(f"Bot: Commands | Action: MenuCommand | user_id={user_id}")

    orchestrator = container.features.get("bot_menu")
    if not orchestrator:
        logger.error("Bot: Commands | Action: MenuCommand | error=OrchestratorNotFound")
        return

    try:
        director = Director(
            container=container,
            state=state,
            session_key=user_id,
            context_id=message.chat.id,
            trigger_id=message.message_id,
        )
        view_dto = await orchestrator.handle_entry(director=director)

        if container.view_sender:
            await container.view_sender.send(view_dto)
            logger.debug(f"Bot: Commands | Action: MenuCommandSuccess | user_id={user_id}")
    except Exception as e:
        logger.error(f"Bot: Commands | Action: MenuCommandFailed | user_id={user_id} | error={e}")

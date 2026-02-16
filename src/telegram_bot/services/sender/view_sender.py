import contextlib

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger as log

from src.telegram_bot.infrastructure.redis.managers.sender.sender_manager import SenderManager
from src.telegram_bot.services.base import UnifiedViewDTO, ViewResultDTO


class ViewSender:
    """
    Сервис-почтальон.
    Отвечает за отправку и обновление сообщений (Menu и Content).
    """

    def __init__(
        self,
        bot: Bot,
        sender_manager: SenderManager,
    ):
        self.bot = bot
        self.manager = sender_manager

        self.key: int | str | None = None
        self.chat_id: int | str | None = None
        self.is_channel: bool = False
        self.message_thread_id: int | None = None

    async def send(self, view: UnifiedViewDTO):
        """
        Основной метод синхронизации UI.
        """
        if not view.session_key or not view.chat_id:
            log.error("ViewSender: session_key and chat_id are required in UnifiedViewDTO")
            return

        self.key = view.session_key
        self.chat_id = view.chat_id
        self.message_thread_id = view.message_thread_id

        # Максимально надежное определение типа чата (User vs Channel/Topic)
        # 1. По явному режиму
        # 2. По отрицательному ID чата (стандарт Telegram для групп/каналов)
        # 3. По наличию thread_id
        self.is_channel = (
            view.mode in ("channel", "topic")
            or (isinstance(self.chat_id, int) and self.chat_id < 0)
            or str(self.chat_id).startswith("-")
            or self.message_thread_id is not None
        )

        ui_coords = await self.manager.get_coords(self.key, self.is_channel)

        log.debug(f"ViewSender | key={self.key} is_channel={self.is_channel} coords={ui_coords}")

        if view.clean_history:
            log.debug(f"ViewSender | Cleaning history for key={self.key}")
            await self._delete_previous_interface(ui_coords)
            ui_coords = {}
            await self.manager.clear_coords(self.key, self.is_channel)

        old_menu_id = ui_coords.get("menu_msg_id")
        new_menu_id = await self._process_message(view_dto=view.menu, old_message_id=old_menu_id, log_prefix="MENU")

        old_content_id = ui_coords.get("content_msg_id")
        new_content_id = await self._process_message(
            view_dto=view.content, old_message_id=old_content_id, log_prefix="CONTENT"
        )

        updates = {}
        if new_menu_id and new_menu_id != old_menu_id:
            updates["menu_msg_id"] = new_menu_id
        if new_content_id and new_content_id != old_content_id:
            updates["content_msg_id"] = new_content_id

        if updates:
            await self.manager.update_coords(self.key, updates, self.is_channel)

    async def _delete_previous_interface(self, ui_coords: dict):
        """Пытается удалить старые сообщения."""
        if not self.chat_id:
            return

        menu_id = ui_coords.get("menu_msg_id")
        content_id = ui_coords.get("content_msg_id")

        if menu_id:
            with contextlib.suppress(TelegramAPIError):
                await self.bot.delete_message(chat_id=self.chat_id, message_id=menu_id)

        if content_id:
            with contextlib.suppress(TelegramAPIError):
                await self.bot.delete_message(chat_id=self.chat_id, message_id=content_id)

    async def _process_message(
        self, view_dto: ViewResultDTO | None, old_message_id: int | None, log_prefix: str
    ) -> int | None:
        if not view_dto or not self.chat_id:
            return old_message_id

        # Если у нас есть ID старого сообщения — пытаемся его отредактировать
        if old_message_id:
            try:
                log.debug(f"ViewSender [{log_prefix}] | Editing message {old_message_id} in chat {self.chat_id}")
                await self.bot.edit_message_text(
                    chat_id=self.chat_id, message_id=old_message_id, text=view_dto.text, reply_markup=view_dto.kb
                )
                return old_message_id
            except TelegramAPIError as e:
                log.warning(f"ViewSender [{log_prefix}] | Edit failed: {e}")

        # Если старого ID нет или редактирование не удалось — отправляем новое
        try:
            log.debug(f"ViewSender [{log_prefix}] | Sending new message to chat {self.chat_id}")
            sent = await self.bot.send_message(
                chat_id=self.chat_id,
                text=view_dto.text,
                reply_markup=view_dto.kb,
                message_thread_id=self.message_thread_id,
            )
            return sent.message_id
        except TelegramAPIError as e:
            log.error(f"ViewSender [{log_prefix}] | Send error: {e}")
            return None

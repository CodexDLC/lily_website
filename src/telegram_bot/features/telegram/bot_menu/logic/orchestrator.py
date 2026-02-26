from typing import Any

from loguru import logger

from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.features.telegram.bot_menu.contracts.menu_contract import MenuDiscoveryProvider
from src.telegram_bot.features.telegram.bot_menu.resources.dto import MenuContext
from src.telegram_bot.features.telegram.bot_menu.ui.menu_ui import BotMenuUI
from src.telegram_bot.services.base.base_orchestrator import BaseBotOrchestrator
from src.telegram_bot.services.base.view_dto import UnifiedViewDTO


class BotMenuOrchestrator(BaseBotOrchestrator):
    """
    Universal menu orchestrator (Dashboards).
    """

    def __init__(self, discovery_provider: MenuDiscoveryProvider, settings: BotSettings):
        super().__init__(expected_state=None)
        self.discovery = discovery_provider
        self.settings = settings
        self.ui = BotMenuUI()

    async def handle_callback(self, ctx: MenuContext) -> UnifiedViewDTO | None:
        """
        Callback handler.
        """
        logger.debug(
            f"Bot: BotMenuOrchestrator | Action: Callback | user_id={ctx.user_id} | action={ctx.action} | target={ctx.target}"
        )

        if ctx.action == "open":
            return await self.handle_entry(ctx.user_id, chat_id=ctx.chat_id, payload=ctx.target)

        if ctx.action == "select":
            return await self.handle_menu_click(ctx.target or "", ctx.user_id, chat_id=ctx.chat_id)

        return None

    async def handle_entry(self, user_id: int, chat_id: int | None = None, payload: Any = None) -> UnifiedViewDTO:
        """
        Entry point.
        """
        target_menu = payload if isinstance(payload, str) else "bot_menu"
        effective_chat_id = chat_id or user_id
        logger.info(f"Bot: BotMenuOrchestrator | Action: Entry | user_id={user_id} | target={target_menu}")
        return await self.render_dashboard(user_id, chat_id=effective_chat_id, mode=target_menu)

    async def render_dashboard(self, user_id: int, chat_id: int, mode: str = "bot_menu") -> UnifiedViewDTO:
        """
        Renders the dashboard.
        """
        is_admin_mode = mode == "dashboard_admin"
        logger.debug(f"Bot: BotMenuOrchestrator | Action: RenderDashboard | user_id={user_id} | mode={mode}")

        available_features = self.discovery.get_menu_buttons(is_admin=is_admin_mode)

        if is_admin_mode and not self._is_user_admin(user_id):
            logger.warning(f"Bot: BotMenuOrchestrator | Action: AccessDenied | user_id={user_id} | mode={mode}")
            return await self.render_dashboard(user_id, chat_id=chat_id, mode="bot_menu")

        menu_view = self.ui.render_dashboard(available_features, mode=mode)

        return UnifiedViewDTO(menu=menu_view, content=None, chat_id=chat_id, session_key=user_id)

    async def handle_menu_click(self, target: str, user_id: int, chat_id: int) -> UnifiedViewDTO | None:
        """
        Menu button click logic.
        """
        logger.info(f"Bot: BotMenuOrchestrator | Action: MenuClick | user_id={user_id} | target={target}")

        # 1. Dashboard switching
        if target in ["dashboard_admin", "bot_menu"]:
            return await self.render_dashboard(user_id, chat_id=chat_id, mode=target)

        # 2. Feature navigation
        features_config = self.discovery.get_menu_buttons()
        target_config = features_config.get(target)

        if not target_config or not self._check_access(user_id, target_config):
            logger.warning(
                f"Bot: BotMenuOrchestrator | Action: FeatureAccessDenied | user_id={user_id} | target={target}"
            )
            return None

        # Use Director for feature transition
        target_feature = target_config.get("target_state", target)
        logger.debug(
            f"Bot: BotMenuOrchestrator | Action: RedirectToFeature | user_id={user_id} | feature={target_feature}"
        )
        return await self.director.set_scene(feature=target_feature, payload=None)

    def _is_user_admin(self, user_id: int) -> bool:
        return user_id in self.settings.owner_ids_list or user_id in self.settings.superuser_ids_list

    def _check_access(self, user_id: int, config: dict[str, Any]) -> bool:
        if config.get("is_superuser"):
            return user_id in self.settings.superuser_ids_list
        if config.get("is_admin"):
            return self._is_user_admin(user_id)
        return True

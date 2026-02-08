from loguru import logger as log

from src.shared.core.config import CommonSettings


class BotSettings(CommonSettings):
    """
    Настройки для Telegram Bot.
    Определяет две ключевые роли:
    - Superuser: Разработчик/Техподдержка (полный доступ).
    - Owner: Владелец бота/бизнеса (доступ к админке).
    """

    # --- Bot ---
    bot_token: str

    # --- Channels ---
    bug_report_channel_id: int | None = None
    
    # --- Roles (ENV) ---
    # ID суперпользователей (разработчиков), через запятую
    superuser_ids: str = ""
    
    # ID владельцев бота (администраторов бизнеса), через запятую
    owner_ids: str = ""

    # --- Data mode ---
    # "api"    — bot talks to FastAPI/Django backend via REST (no direct DB)
    # "direct" — bot has its own database (uses SQLAlchemy + Alembic)
    BOT_DATA_MODE: str = "api"

    # --- Database (only when BOT_DATA_MODE=direct) ---
    DATABASE_URL: str | None = None
    DB_SCHEMA: str = "bot_app"  # PostgreSQL schema for table isolation

    # --- Backend API (only when BOT_DATA_MODE=api) ---
    backend_api_url: str = "http://localhost:8000"
    backend_api_key: str | None = None
    backend_api_timeout: float = 10.0

    @property
    def superuser_ids_list(self) -> list[int]:
        return self._parse_ids(self.superuser_ids)

    @property
    def owner_ids_list(self) -> list[int]:
        return self._parse_ids(self.owner_ids)

    @property
    def roles(self) -> dict[str, list[int]]:
        """
        Словарь ролей для проверки доступа.
        """
        superusers = self.superuser_ids_list
        owners = self.owner_ids_list
        
        return {
            "superuser": superusers,
            # Владелец + Суперюзер (суперюзер имеет права владельца)
            "owner": list(set(owners + superusers)),
            # Алиас для совместимости
            "admin": list(set(owners + superusers)),
        }

    def _parse_ids(self, ids_str: str) -> list[int]:
        """Парсит строку '123,456' в список чисел."""
        if not ids_str:
            return []
        try:
            return [int(x.strip()) for x in ids_str.split(",") if x.strip()]
        except ValueError:
            log.warning(f"BotSettings | Failed to parse IDs='{ids_str}'. Check .env format.")
            return []

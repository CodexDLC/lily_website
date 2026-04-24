import json
import os
from pathlib import Path
from urllib.parse import quote_plus

from codex_core.settings import BaseCommonSettings
from loguru import logger as log
from pydantic import Field, field_validator
from pydantic_settings import SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE_PATH = ROOT_DIR / ".env"


class BotSettings(BaseCommonSettings):
    """Configuration settings for the Telegram Bot."""

    # --- Redis (bot-specific) ---
    redis_site_settings_key: str = "site_settings_hash"

    # --- Logging ---
    log_level_console: str = "DEBUG"
    log_level_file: str = "DEBUG"
    log_rotation: str = "10 MB"
    log_dir_name: str = "logs"

    # --- System ---
    system_user_id: int = 2_000_000_000

    # --- Bot ---
    bot_token: str
    secret_key: str = Field(alias="SECRET_KEY")

    # --- Channels & Topics ---
    telegram_admin_channel_id: int | None = None
    telegram_notification_topic_id: int | None = None
    telegram_topics: dict[str, int] = {}

    @field_validator("telegram_topics", mode="before")
    @classmethod
    def parse_telegram_topics(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return {}
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    return parsed
                log.warning(f"TELEGRAM_TOPICS is not a dict after parsing: {type(parsed)}")
                return {}
            except json.JSONDecodeError as e:
                log.error(f"Failed to parse TELEGRAM_TOPICS as JSON: {e}")
                return {}
        return v or {}

    # --- Roles (ENV) ---
    superuser_ids: str = ""
    owner_ids: str = ""

    # --- Data mode ---
    BOT_DATA_MODE: str = "api"

    # --- Database (only when BOT_DATA_MODE=direct) ---
    DATABASE_URL: str | None = None
    DB_SCHEMA: str = "bot_app"

    # --- Backend API ---
    backend_api_url_env: str = Field(default="http://localhost:8000", alias="BACKEND_API_URL")
    backend_api_key: str | None = Field(default=None, alias="BACKEND_API_KEY")
    backend_api_timeout: float = 10.0

    # --- Computed properties ---

    @property
    def is_inside_docker(self) -> bool:
        return os.environ.get("IS_DOCKER", "False").lower() in ("true", "1", "t") or os.path.exists("/.dockerenv")

    @property
    def service_name_suffix(self) -> str:
        return "" if self.is_inside_docker else "_local"

    @property
    def effective_redis_host(self) -> str:
        if self.redis_host != "localhost":
            return self.redis_host
        return "redis" if self.is_inside_docker else "localhost"

    @property
    def redis_url(self) -> str:
        host = self.effective_redis_host
        password = self.redis_password
        if password:
            password = password.strip("'\"").strip()
        if password:
            encoded_password = quote_plus(password)
            return f"redis://:{encoded_password}@{host}:{self.redis_port}"
        return f"redis://{host}:{self.redis_port}"

    @property
    def log_dir(self) -> str:
        return str(ROOT_DIR / self.log_dir_name)

    @log_dir.setter
    def log_dir(self, value: str) -> None:
        """Protocol requires settable variable."""
        pass

    @property
    def log_file_debug(self) -> str:
        service_name = f"{os.environ.get('PROJECT_NAME', 'service')}{self.service_name_suffix}"
        return f"{self.log_dir}/{service_name}/debug.log"

    @property
    def log_file_errors(self) -> str:
        service_name = f"{os.environ.get('PROJECT_NAME', 'service')}{self.service_name_suffix}"
        return f"{self.log_dir}/{service_name}/errors.json"

    @property
    def api_url(self) -> str:
        url = self.backend_api_url_env
        if url and "localhost" not in url and "127.0.0.1" not in url:
            return url.rstrip("/")
        base = "http://localhost:8000" if self.debug else "http://backend:8000"
        return base

    @property
    def backend_api_url(self) -> str:
        return self.api_url

    @property
    def superuser_ids_list(self) -> list[int]:
        return self._parse_ids(self.superuser_ids)

    @property
    def owner_ids_list(self) -> list[int]:
        return self._parse_ids(self.owner_ids)

    @property
    def roles(self) -> dict[str, list[int]]:
        superusers = self.superuser_ids_list
        owners = self.owner_ids_list
        return {
            "superuser": superusers,
            "owner": list(set(owners + superusers)),
            "admin": list(set(owners + superusers)),
        }

    def _parse_ids(self, ids_str: str) -> list[int]:
        if not ids_str:
            return []
        try:
            return [int(x.strip()) for x in ids_str.split(",") if x.strip()]
        except ValueError:
            log.warning(f"BotSettings | Failed to parse IDs='{ids_str}'. Check .env format.")
            return []

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

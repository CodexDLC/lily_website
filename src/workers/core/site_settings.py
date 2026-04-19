from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class WorkerSiteSettings(BaseModel):
    """Subset of SiteSettings needed by workers."""

    company_name: str = "LILY Beauty Salon"
    site_base_url: str = "https://lily-salon.de/"
    logo_url: str = "/static/img/_source/logo_lily.png"
    email: str = "info@lily-salon.de"
    url_path_contact_form: str = "/contacts/"
    url_path_confirm: str = "/cabinet/appointments/confirm/{token}/"
    url_path_cancel: str = "/cabinet/appointments/cancel/{token}/"
    url_path_reschedule: str = "/cabinet/appointments/reschedule/{token}/"

    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = False
    smtp_use_ssl: bool = True
    sendgrid_api_key: str | None = None

    model_config = {"extra": "ignore"}


class SiteSettingsRedisReader:
    """Read SiteSettings from the Django Redis hash, with old-key fallback."""

    def __init__(self, redis_client: Any, *, project_namespace: str, base_key: str = "site_settings") -> None:
        self.redis_client = redis_client
        self.project_namespace = project_namespace.strip(":")
        self.base_key = base_key

    async def load(self) -> WorkerSiteSettings:
        for key in self._candidate_keys():
            raw = await self.redis_client.hgetall(key)
            if raw:
                return WorkerSiteSettings(**self._normalize(raw))
        return WorkerSiteSettings()

    def _candidate_keys(self) -> list[str]:
        namespaced = f"{self.project_namespace}:{self.base_key}" if self.project_namespace else self.base_key
        return [namespaced, self.base_key, "site_settings_hash"]

    @staticmethod
    def _normalize(raw: dict[Any, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key, value in raw.items():
            str_key = key.decode() if isinstance(key, bytes) else str(key)
            if isinstance(value, bytes):
                value = value.decode()
            normalized[str_key] = value
        return normalized


def merge_email_settings(site_settings: WorkerSiteSettings, worker_settings: Any) -> WorkerSiteSettings:
    """Apply env secrets/fallbacks over public SiteSettings values."""

    data = site_settings.model_dump()
    fallbacks = {
        "smtp_host": worker_settings.SMTP_HOST,
        "smtp_port": worker_settings.SMTP_PORT,
        "smtp_user": worker_settings.SMTP_USER,
        "smtp_password": worker_settings.SMTP_PASSWORD,
        "smtp_from_email": worker_settings.SMTP_FROM_EMAIL,
        "smtp_use_tls": worker_settings.SMTP_USE_TLS,
        "smtp_use_ssl": worker_settings.SMTP_USE_SSL,
        "sendgrid_api_key": worker_settings.SENDGRID_API_KEY,
    }
    for field, fallback in fallbacks.items():
        if data.get(field) in (None, "") and fallback not in (None, ""):
            data[field] = fallback
    return WorkerSiteSettings(**data)

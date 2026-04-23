from __future__ import annotations

from typing import TYPE_CHECKING

from codex_django.core.redis.managers.static_content import StaticContentManager
from django.conf import settings
from django.utils import translation

if TYPE_CHECKING:
    from django.db import models


class ProjectStaticContentManager(StaticContentManager):
    """Language-aware Redis manager for editable static translations."""

    def _normalize_lang(self, lang_code: str | None = None) -> str:
        lang = (lang_code or translation.get_language() or settings.LANGUAGE_CODE).split("-")[0]
        supported = {code for code, _ in getattr(settings, "LANGUAGES", [])}
        return lang if lang in supported else settings.LANGUAGE_CODE.split("-")[0]

    def _cache_key_for_lang(self, lang_code: str | None = None) -> str:
        return f"{self.cache_key}:{self._normalize_lang(lang_code)}"

    async def aload_cached(
        self,
        model_cls: type[models.Model],
        lang_code: str | None = None,
    ) -> dict[str, str]:
        if self._is_disabled():
            return {}

        cache_key = self._cache_key_for_lang(lang_code)
        async with self.async_hash() as h:
            result = await h.get_all(self.make_key(cache_key))
        return result or {}

    def load_cached(
        self,
        model_cls: type[models.Model],
        lang_code: str | None = None,
    ) -> dict[str, str]:
        if self._is_disabled():
            return {}

        lang = self._normalize_lang(lang_code)
        cache_key = self._cache_key_for_lang(lang)

        with self.sync_hash() as h:
            data = h.get_all(self.make_key(cache_key))

        if not data:
            with translation.override(lang):
                rows = model_cls.objects.all()  # type: ignore[attr-defined]
                data = {str(obj.key): str(obj.content or "") for obj in rows}
            if data:
                self.save_mapping(data, lang_code=lang)

        return data or {}

    async def asave_mapping(self, data: dict[str, str], lang_code: str | None = None) -> None:
        if self._is_disabled() or not data:
            return

        cache_key = self._cache_key_for_lang(lang_code)
        async with self.async_hash() as h:
            await h.set_fields(self.make_key(cache_key), data)

    def save_mapping(self, data: dict[str, str], lang_code: str | None = None) -> None:
        if self._is_disabled() or not data:
            return

        cache_key = self._cache_key_for_lang(lang_code)
        with self.sync_hash() as h:
            h.set_fields(self.make_key(cache_key), data)

    def clear_language(self, lang_code: str | None = None) -> None:
        if self._is_disabled():
            return

        cache_key = self._cache_key_for_lang(lang_code)
        with self.sync_hash() as h:
            h.delete(self.make_key(cache_key))

    def clear_all_languages(self) -> None:
        if self._is_disabled():
            return

        for lang_code, _ in getattr(settings, "LANGUAGES", []):
            self.clear_language(lang_code)


def get_static_content_manager() -> ProjectStaticContentManager:
    return ProjectStaticContentManager()

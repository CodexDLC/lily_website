from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar


class EmailTemplate(ABC):
    key: ClassVar[str]
    label: ClassVar[str]
    arq_template_name: ClassVar[str]
    supported_locales: ClassVar[set[str]]

    @abstractmethod
    def build_context(self, body_text: str, extra: dict) -> dict:
        """Prepares context_data for the arq task."""


class BasicTemplate(EmailTemplate):
    key = "basic"
    label = "Basic (header + text + footer)"
    arq_template_name = "mk_basic"
    supported_locales = {"de"}

    def build_context(self, body_text: str, extra: dict) -> dict:
        return {
            "body_text": body_text,
            **extra,
        }


class TemplateRegistry:
    def __init__(self) -> None:
        self._items: dict[str, EmailTemplate] = {}

    def register(self, tpl: EmailTemplate) -> None:
        self._items[tpl.key] = tpl

    def get(self, key: str) -> EmailTemplate:
        return self._items[key]

    def list_for_locale(self, locale: str) -> list[EmailTemplate]:
        return [t for t in self._items.values() if locale in t.supported_locales]

    def choices_for_locale(self, locale: str) -> list[tuple[str, str]]:
        return [(t.key, t.label) for t in self.list_for_locale(locale)]


template_registry = TemplateRegistry()
template_registry.register(BasicTemplate())

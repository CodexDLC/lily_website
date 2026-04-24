from __future__ import annotations

from typing import Protocol


class LocaleResolver(Protocol):
    def resolve(self, recipient: object) -> str: ...
    def supported(self) -> list[str]: ...


class SingleLocaleResolver:
    def __init__(self, locale: str = "de") -> None:
        self._locale = locale

    def resolve(self, recipient: object) -> str:
        return self._locale

    def supported(self) -> list[str]:
        return [self._locale]

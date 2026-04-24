from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass
class AudienceFilter:
    email_opt_in: bool = True
    has_valid_email: bool = True
    locales: list[str] | None = None
    has_appointment_since: date | None = None
    service_ids: list[int] | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.has_appointment_since:
            d["has_appointment_since"] = self.has_appointment_since.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> AudienceFilter:
        appointment_since = data.get("has_appointment_since")
        if appointment_since and isinstance(appointment_since, str):
            appointment_since = date.fromisoformat(appointment_since)
        return cls(
            email_opt_in=data.get("email_opt_in", True),
            has_valid_email=data.get("has_valid_email", True),
            locales=data.get("locales"),
            has_appointment_since=appointment_since,
            service_ids=data.get("service_ids"),
        )


@dataclass
class RecipientDraft:
    recipient_id: int
    email: str
    first_name: str
    last_name: str
    locale: str
    unsubscribe_token: str


class AudienceBuilder(Protocol):
    def count(self, f: AudienceFilter) -> int: ...
    def materialize(self, f: AudienceFilter) -> Iterable[RecipientDraft]: ...

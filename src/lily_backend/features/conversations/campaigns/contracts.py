from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CampaignRecipientContract(Protocol):
    """What the library expects from the project's recipient model."""

    email: str | None
    first_name: str
    last_name: str
    consent_marketing: bool
    unsubscribe_token: object  # UUID

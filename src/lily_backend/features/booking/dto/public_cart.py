"""Public booking cart DTO and session service.

The cart is stored in Django's session under SESSION_KEY.
It is session-only (no DB draft) — cleared after successful commit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpRequest

SESSION_KEY = "booking_pub_v1"

MODE_SAME_DAY = "same_day"
MODE_MULTI_DAY = "multi_day"


@dataclass
class PublicCartItem:
    service_id: int
    service_title: str
    duration: int  # minutes
    price: Decimal
    # multi-day: assigned per-item; None in same_day mode
    date: str | None = None  # "YYYY-MM-DD"
    time: str | None = None  # "HH:MM"

    def to_dict(self) -> dict:
        return {
            "service_id": self.service_id,
            "service_title": self.service_title,
            "duration": self.duration,
            "price": str(self.price),
            "date": self.date,
            "time": self.time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PublicCartItem:
        return cls(
            service_id=data["service_id"],
            service_title=data["service_title"],
            duration=data["duration"],
            price=Decimal(data["price"]),
            date=data.get("date"),
            time=data.get("time"),
        )


@dataclass
class PublicCart:
    items: list[PublicCartItem] = field(default_factory=list)
    mode: str = MODE_SAME_DAY
    stage: int = 1  # 1: Review, 2: Schedule, 3: Confirm
    date: str | None = None  # same_day flow
    time: str | None = None  # same_day flow
    contact: dict = field(default_factory=lambda: {"name": "", "phone": "", "email": ""})

    # --- Service operations ---

    def add(self, item: PublicCartItem) -> None:
        """Add a service item to the cart (caller is responsible for conflict rules)."""
        if not any(i.service_id == item.service_id for i in self.items):
            self.items.append(item)

    def remove(self, service_id: int) -> None:
        self.items = [i for i in self.items if i.service_id != service_id]

    def remove_ids(self, service_ids: list[int]) -> None:
        """Bulk remove by IDs (used by conflict rule enforcement)."""
        ids_set = set(service_ids)
        self.items = [i for i in self.items if i.service_id not in ids_set]

    def has(self, service_id: int) -> bool:
        return any(i.service_id == service_id for i in self.items)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def set_item_slot(self, service_id: int, date: str, time: str) -> None:
        """Assign a date+time to a specific cart item (multi-day mode)."""
        for item in self.items:
            if item.service_id == service_id:
                item.date = date
                item.time = time
                return

    # --- Aggregations ---

    def service_ids(self) -> list[int]:
        return [i.service_id for i in self.items]

    def total_price(self) -> Decimal:
        return sum((i.price for i in self.items), Decimal("0"))

    def total_duration(self) -> int:
        return sum(i.duration for i in self.items)

    # --- Readiness checks ---

    def is_ready_same_day(self) -> bool:
        """Cart has items, a date and a time selected."""
        return bool(self.items) and bool(self.date) and bool(self.time)

    def is_ready_multi_day(self) -> bool:
        """All cart items have a date and time assigned."""
        return bool(self.items) and all(i.date and i.time for i in self.items)

    def is_group_booking(self) -> bool:
        """True when 2+ services on the same day — triggers AppointmentGroup creation."""
        return self.mode == MODE_SAME_DAY and len(self.items) >= 2

    # --- Serialisation ---

    def to_dict(self) -> dict:
        return {
            "items": [i.to_dict() for i in self.items],
            "mode": self.mode,
            "stage": self.stage,
            "date": self.date,
            "time": self.time,
            "contact": self.contact,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PublicCart:
        return cls(
            items=[PublicCartItem.from_dict(d) for d in data.get("items", [])],
            mode=data.get("mode", MODE_SAME_DAY),
            stage=data.get("stage", 1),
            date=data.get("date"),
            time=data.get("time"),
            contact=data.get("contact", {"name": "", "phone": "", "email": ""}),
        )


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------


def get_cart(request: HttpRequest) -> PublicCart:
    """Load cart from session, returning an empty cart if none exists."""
    data = request.session.get(SESSION_KEY)
    if data:
        return PublicCart.from_dict(data)
    return PublicCart()


def save_cart(request: HttpRequest, cart: PublicCart) -> None:
    """Persist cart back to session."""
    request.session[SESSION_KEY] = cart.to_dict()
    request.session.modified = True


def clear_cart(request: HttpRequest) -> None:
    """Remove cart from session after successful commit."""
    request.session.pop(SESSION_KEY, None)
    request.session.modified = True

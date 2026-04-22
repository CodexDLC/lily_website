from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, Any, ClassVar

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from system.models import LoyaltyProfile, UserProfile


@dataclass(frozen=True)
class LoyaltyDisplayData:
    level: int
    best_level: int
    segment: str
    label: str
    tone: str
    progress_percent: int
    filled_stars: list[int]
    empty_stars: list[int]

    @property
    def staff_label(self) -> str:
        return f"{self.label} - {self.level}/4"


class LoyaltyService:
    """Calculate and cache loyalty display state for registered client profiles."""

    MIN_MULTIPLIER: ClassVar[Decimal] = Decimal("0.70")
    MAX_MULTIPLIER: ClassVar[Decimal] = Decimal("1.30")
    LEVEL_THRESHOLDS: ClassVar[tuple[Decimal, Decimal, Decimal, Decimal]] = (
        Decimal("0"),
        Decimal("200"),
        Decimal("500"),
        Decimal("1000"),
    )
    SEGMENTS: ClassVar[dict[int, tuple[str, str, str]]] = {
        1: ("new", str(_("New")), "secondary"),
        2: ("regular", str(_("Regular")), "info"),
        3: ("loyal", str(_("Loyal")), "success"),
        4: ("vip", "VIP", "warning"),
    }

    @classmethod
    def get_or_refresh_for_profile(cls, profile: UserProfile) -> LoyaltyProfile:
        from system.models import LoyaltyProfile

        loyalty, _created = LoyaltyProfile.objects.get_or_create(profile=profile)
        source_hash, calculation = cls._calculate(profile)

        if loyalty.source_hash == source_hash:
            return loyalty

        previous_best = loyalty.best_level or 1
        loyalty.level = calculation["level"]
        loyalty.best_level = max(previous_best, calculation["level"])
        loyalty.progress_percent = calculation["progress_percent"]
        loyalty.effective_spend_score = calculation["effective_spend_score"]
        loyalty.behavior_multiplier = calculation["behavior_multiplier"]
        loyalty.source_hash = source_hash
        loyalty.calculated_at = timezone.now()
        loyalty.stats = calculation["stats"]
        loyalty.save(
            update_fields=[
                "level",
                "best_level",
                "progress_percent",
                "effective_spend_score",
                "behavior_multiplier",
                "source_hash",
                "calculated_at",
                "stats",
                "updated_at",
            ]
        )
        return loyalty

    @classmethod
    def get_display_data(cls, loyalty: LoyaltyProfile | None) -> LoyaltyDisplayData:
        level = loyalty.level if loyalty else 1
        best_level = loyalty.best_level if loyalty else level
        progress_percent = loyalty.progress_percent if loyalty else 0
        segment, label, tone = cls.SEGMENTS.get(level, cls.SEGMENTS[1])
        return LoyaltyDisplayData(
            level=level,
            best_level=best_level,
            segment=segment,
            label=label,
            tone=tone,
            progress_percent=progress_percent,
            filled_stars=list(range(level)),
            empty_stars=list(range(4 - level)),
        )

    @classmethod
    def get_display_for_profile(cls, profile: UserProfile | None) -> LoyaltyDisplayData | None:
        if profile is None:
            return None
        return cls.get_display_data(cls.get_or_refresh_for_profile(profile))

    @classmethod
    def _calculate(cls, profile: UserProfile) -> tuple[str, dict[str, Any]]:
        rows = cls._source_rows(profile)
        source_hash = cls._hash_rows(profile_id=profile.pk, rows=rows)

        paid_spend = sum((row["amount"] for row in rows if row["status"] == "completed"), Decimal("0"))
        completed_count = sum(1 for row in rows if row["status"] == "completed")
        no_show_count = sum(1 for row in rows if row["status"] == "no_show")
        late_cancel_count = sum(1 for row in rows if row["is_late_cancel"])
        overdue_pending_count = sum(1 for row in rows if row["is_overdue_pending"])
        reschedule_count = sum(1 for row in rows if row["is_reschedule"])
        current_completed_streak = cls._completed_streak(rows)

        multiplier = (
            Decimal("1.00")
            + min(Decimal(completed_count) * Decimal("0.015"), Decimal("0.20"))
            + min(Decimal(current_completed_streak) * Decimal("0.02"), Decimal("0.10"))
            - Decimal(no_show_count) * Decimal("0.08")
            - Decimal(late_cancel_count) * Decimal("0.05")
            - Decimal(overdue_pending_count) * Decimal("0.04")
            - Decimal(reschedule_count) * Decimal("0.02")
        )
        multiplier = min(max(multiplier, cls.MIN_MULTIPLIER), cls.MAX_MULTIPLIER).quantize(Decimal("0.01"))
        effective_score = (paid_spend * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        level, progress_percent = cls._level_and_progress(effective_score)

        return source_hash, {
            "level": level,
            "progress_percent": progress_percent,
            "effective_spend_score": effective_score,
            "behavior_multiplier": multiplier,
            "stats": {
                "paid_spend": str(paid_spend.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "completed_count": completed_count,
                "current_completed_streak": current_completed_streak,
                "no_show_count": no_show_count,
                "late_cancel_count": late_cancel_count,
                "overdue_pending_count": overdue_pending_count,
                "reschedule_count": reschedule_count,
                "appointment_count": len(rows),
            },
        }

    @classmethod
    def _source_rows(cls, profile: UserProfile) -> list[dict[str, Any]]:
        client = getattr(profile.user, "client_profile", None) if profile.user_id else None
        if client is None or not client.pk:
            return []

        now = timezone.now()
        return [cls._source_row(appt, now=now) for appt in client.appointments.all().order_by("datetime_start", "id")]

    @staticmethod
    def _source_row(appt: Any, *, now: Any) -> dict[str, Any]:
        amount = appt.price_actual if appt.price_actual is not None else appt.price
        cancelled_at = appt.cancelled_at
        is_late_cancel = (
            appt.status == "cancelled"
            and appt.cancel_reason == "client"
            and cancelled_at is not None
            and appt.datetime_start is not None
            and timedelta(0) <= appt.datetime_start - cancelled_at < timedelta(hours=24)
        )
        is_overdue_pending = appt.status == "pending" and appt.datetime_start < now
        is_reschedule = appt.status == "reschedule_proposed" or appt.cancel_reason == "reschedule"

        return {
            "id": appt.pk,
            "status": appt.status,
            "datetime_start": appt.datetime_start.isoformat(),
            "amount": Decimal(amount),
            "price": Decimal(appt.price),
            "price_actual": Decimal(appt.price_actual) if appt.price_actual is not None else None,
            "cancelled_at": cancelled_at.isoformat() if cancelled_at else None,
            "cancel_reason": appt.cancel_reason,
            "is_late_cancel": is_late_cancel,
            "is_past": appt.datetime_start < now,
            "is_overdue_pending": is_overdue_pending,
            "is_reschedule": is_reschedule,
        }

    @staticmethod
    def _completed_streak(rows: list[dict[str, Any]]) -> int:
        streak = 0
        past_rows = [row for row in rows if row["is_past"]]
        for row in sorted(past_rows, key=lambda item: (item["datetime_start"], item["id"]), reverse=True):
            if row["status"] != "completed":
                break
            streak += 1
        return streak

    @classmethod
    def _level_and_progress(cls, score: Decimal) -> tuple[int, int]:
        thresholds = cls.LEVEL_THRESHOLDS
        if score >= thresholds[3]:
            return 4, 100
        if score >= thresholds[2]:
            return 3, cls._progress_between(score, thresholds[2], thresholds[3])
        if score >= thresholds[1]:
            return 2, cls._progress_between(score, thresholds[1], thresholds[2])
        return 1, cls._progress_between(score, thresholds[0], thresholds[1])

    @staticmethod
    def _progress_between(score: Decimal, start: Decimal, end: Decimal) -> int:
        if end <= start:
            return 100
        value = ((score - start) / (end - start) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return int(min(max(value, Decimal("0")), Decimal("100")))

    @staticmethod
    def _hash_rows(*, profile_id: int | None, rows: list[dict[str, Any]]) -> str:
        payload = {
            "profile_id": profile_id,
            "rows": rows,
            "version": 1,
        }
        data = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

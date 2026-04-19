from decimal import Decimal
from unittest.mock import MagicMock, patch

from system.services.loyalty import LoyaltyService


class TestLoyaltyService:
    def test_completed_streak_logic(self):
        rows = [
            {"id": 1, "datetime_start": "2026-04-01T10:00", "status": "completed", "is_past": True},
            {"id": 2, "datetime_start": "2026-04-02T10:00", "status": "completed", "is_past": True},
            {"id": 3, "datetime_start": "2026-04-03T10:00", "status": "cancelled", "is_past": True},
            {"id": 4, "datetime_start": "2026-04-04T10:00", "status": "completed", "is_past": True},
        ]
        # Should be 1, because the streak is broken by the cancellation at id=3 (sorting reverse)
        assert LoyaltyService._completed_streak(rows) == 1

    def test_level_and_progress_calculation(self):
        # Thresholds: 0, 200, 500, 1000

        # Level 1: 100 score -> 50% to Level 2 (200)
        level, progress = LoyaltyService._level_and_progress(Decimal("100"))
        assert level == 1
        assert progress == 50

        # Level 2: 350 score -> 50% to Level 3 (500)
        level, progress = LoyaltyService._level_and_progress(Decimal("350"))
        assert level == 2
        assert progress == 50

        # Level 3: 750 score -> 50% to Level 4 (1000)
        level, progress = LoyaltyService._level_and_progress(Decimal("750"))
        assert level == 3
        assert progress == 50

        # Level 4: 1200 score -> 100%
        level, progress = LoyaltyService._level_and_progress(Decimal("1200"))
        assert level == 4
        assert progress == 100

    def test_multiplier_calculation(self):
        # Mock profile and rows
        profile = MagicMock()
        rows = [
            # 5 completed -> +0.075 (5 * 0.015)
            # Streak 3 completed -> +0.06 (3 * 0.02)
            # 1 no_show -> -0.08
            # Total: 1.0 + 0.075 + 0.06 - 0.08 = 1.055
            {
                "status": "completed",
                "amount": Decimal("100"),
                "is_late_cancel": False,
                "is_overdue_pending": False,
                "is_reschedule": False,
                "is_past": True,
                "datetime_start": "2026-04-01",
                "id": 1,
            },
            {
                "status": "completed",
                "amount": Decimal("100"),
                "is_late_cancel": False,
                "is_overdue_pending": False,
                "is_reschedule": False,
                "is_past": True,
                "datetime_start": "2026-04-02",
                "id": 2,
            },
            {
                "status": "completed",
                "amount": Decimal("100"),
                "is_late_cancel": False,
                "is_overdue_pending": False,
                "is_reschedule": False,
                "is_past": True,
                "datetime_start": "2026-04-03",
                "id": 3,
            },
            {
                "status": "completed",
                "amount": Decimal("100"),
                "is_late_cancel": False,
                "is_overdue_pending": False,
                "is_reschedule": False,
                "is_past": False,
                "datetime_start": "2026-04-04",
                "id": 4,
            },
            {
                "status": "completed",
                "amount": Decimal("100"),
                "is_late_cancel": False,
                "is_overdue_pending": False,
                "is_reschedule": False,
                "is_past": False,
                "datetime_start": "2026-04-05",
                "id": 5,
            },
            {
                "status": "completed",
                "amount": Decimal("100"),
                "is_late_cancel": False,
                "is_overdue_pending": False,
                "is_reschedule": False,
                "is_past": True,
                "datetime_start": "2026-04-06",
                "id": 6,
            },
        ]

        with (
            patch.object(LoyaltyService, "_source_rows", return_value=rows),
            patch.object(LoyaltyService, "_hash_rows", return_value="hash"),
        ):
            _hash, result = LoyaltyService._calculate(profile)

            # 1.0 + 6*0.015 + 4*0.02 = 1.0 + 0.09 + 0.08 = 1.17
            assert result["behavior_multiplier"] == Decimal("1.17")
            # Effective score: 600 * 1.17 = 702
            assert result["effective_spend_score"] == Decimal("702.00")
            assert result["level"] == 3

    def test_display_data_mapping(self):
        loyalty = MagicMock()
        loyalty.level = 2
        loyalty.best_level = 3
        loyalty.progress_percent = 45

        data = LoyaltyService.get_display_data(loyalty)
        assert data.level == 2
        assert data.best_level == 3
        assert data.label == "Regular"
        assert data.tone == "info"
        assert len(data.filled_stars) == 2
        assert len(data.empty_stars) == 2

    def test_display_data_none(self):
        data = LoyaltyService.get_display_data(None)
        assert data.level == 1
        assert data.label == "New"
        assert len(data.filled_stars) == 1
        assert len(data.empty_stars) == 3

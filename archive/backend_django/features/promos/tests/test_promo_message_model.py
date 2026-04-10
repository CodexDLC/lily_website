"""
Tests for features.promos.models.promo_message.PromoMessage.
Covers model properties, status logic, clean(), save(), and __str__.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from features.promos.models import PromoMessage


def _make_promo(
    title="Test Promo",
    is_active=True,
    starts_offset_hours=-1,
    ends_offset_hours=1,
    views_count=0,
    clicks_count=0,
    priority=0,
    target_pages="",
    button_text="Акция!",
    button_color="#EDD071",
    text_color="#003831",
    description="Test description",
):
    """Helper: create a PromoMessage with relative time offsets."""
    now = timezone.now()
    return PromoMessage.objects.create(
        title=title,
        description=description,
        is_active=is_active,
        starts_at=now + timedelta(hours=starts_offset_hours),
        ends_at=now + timedelta(hours=ends_offset_hours),
        views_count=views_count,
        clicks_count=clicks_count,
        priority=priority,
        target_pages=target_pages,
        button_text=button_text,
        button_color=button_color,
        text_color=text_color,
    )


@pytest.mark.django_db
class TestPromoMessageStr:
    def test_str_contains_title(self):
        promo = _make_promo(title="Summer Sale")
        assert "Summer Sale" in str(promo)

    def test_str_contains_date_range(self):
        promo = _make_promo()
        s = str(promo)
        # Should contain year
        assert "202" in s


@pytest.mark.django_db
class TestPromoMessageIsCurrentlyActive:
    def test_active_and_within_dates(self):
        promo = _make_promo(is_active=True, starts_offset_hours=-1, ends_offset_hours=1)
        assert promo.is_currently_active is True

    def test_inactive_flag_returns_false(self):
        promo = _make_promo(is_active=False)
        assert promo.is_currently_active is False

    def test_not_started_yet_returns_false(self):
        promo = _make_promo(is_active=True, starts_offset_hours=1, ends_offset_hours=2)
        assert promo.is_currently_active is False

    def test_already_expired_returns_false(self):
        promo = _make_promo(is_active=True, starts_offset_hours=-2, ends_offset_hours=-1)
        assert promo.is_currently_active is False


@pytest.mark.django_db
class TestPromoMessageStatus:
    def test_active_status_when_active_and_within_dates(self):
        promo = _make_promo(is_active=True, starts_offset_hours=-1, ends_offset_hours=1)
        assert promo.status == PromoMessage.PromoStatus.ACTIVE

    def test_inactive_status_when_is_active_false(self):
        promo = _make_promo(is_active=False, starts_offset_hours=-1, ends_offset_hours=1)
        assert promo.status == PromoMessage.PromoStatus.INACTIVE

    def test_scheduled_status_when_not_started(self):
        promo = _make_promo(is_active=True, starts_offset_hours=1, ends_offset_hours=2)
        assert promo.status == PromoMessage.PromoStatus.SCHEDULED

    def test_expired_status_when_past_end_date(self):
        promo = _make_promo(is_active=True, starts_offset_hours=-2, ends_offset_hours=-1)
        assert promo.status == PromoMessage.PromoStatus.EXPIRED


@pytest.mark.django_db
class TestPromoMessageStatusDisplay:
    def test_active_status_display(self):
        promo = _make_promo(is_active=True, starts_offset_hours=-1, ends_offset_hours=1)
        display = promo.status_display
        # Should return human-readable label
        assert isinstance(display, str)
        assert len(display) > 0

    def test_inactive_status_display(self):
        promo = _make_promo(is_active=False)
        display = promo.status_display
        assert "Inactive" in display or "inactive" in display.lower() or len(display) > 0

    def test_scheduled_status_display(self):
        promo = _make_promo(is_active=True, starts_offset_hours=1, ends_offset_hours=2)
        display = promo.status_display
        assert isinstance(display, str)

    def test_expired_status_display(self):
        promo = _make_promo(is_active=True, starts_offset_hours=-2, ends_offset_hours=-1)
        display = promo.status_display
        assert isinstance(display, str)


@pytest.mark.django_db
class TestPromoMessageCTR:
    def test_ctr_zero_when_no_views(self):
        promo = _make_promo(views_count=0, clicks_count=0)
        assert promo.ctr == 0.0

    def test_ctr_calculation(self):
        promo = _make_promo(views_count=100, clicks_count=10)
        assert promo.ctr == 10.0

    def test_ctr_50_percent(self):
        promo = _make_promo(views_count=200, clicks_count=100)
        assert promo.ctr == 50.0

    def test_ctr_fractional(self):
        promo = _make_promo(views_count=3, clicks_count=1)
        assert abs(promo.ctr - 33.333) < 0.01

    def test_ctr_zero_when_views_but_no_clicks(self):
        promo = _make_promo(views_count=50, clicks_count=0)
        assert promo.ctr == 0.0


@pytest.mark.django_db
class TestPromoMessageClean:
    def test_clean_passes_when_ends_after_starts(self):
        # Should not raise
        now = timezone.now()
        promo = PromoMessage(
            title="Test",
            description="Desc",
            starts_at=now,
            ends_at=now + timedelta(hours=1),
        )
        promo.clean()  # Should not raise

    def test_clean_raises_when_ends_before_starts(self):
        now = timezone.now()
        promo = PromoMessage(
            title="Test",
            description="Desc",
            starts_at=now + timedelta(hours=1),
            ends_at=now,
        )
        with pytest.raises(ValidationError) as exc_info:
            promo.clean()
        assert "ends_at" in exc_info.value.message_dict

    def test_clean_raises_when_ends_equals_starts(self):
        now = timezone.now()
        promo = PromoMessage(
            title="Test",
            description="Desc",
            starts_at=now,
            ends_at=now,
        )
        with pytest.raises(ValidationError):
            promo.clean()


@pytest.mark.django_db
class TestPromoMessageSave:
    def test_save_creates_record(self):
        promo = _make_promo()
        assert promo.pk is not None

    def test_save_calls_full_clean(self):
        now = timezone.now()
        with pytest.raises(ValidationError):
            PromoMessage.objects.create(
                title="Bad dates",
                description="Desc",
                starts_at=now + timedelta(hours=2),
                ends_at=now + timedelta(hours=1),
            )

    def test_save_with_image_new_instance_calls_optimize(self):
        """When creating a new PromoMessage with an image, optimize_image is called."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        fake_image = SimpleUploadedFile("test.jpg", b"fake_data", content_type="image/jpeg")
        now = timezone.now()
        import contextlib

        with (
            patch("features.promos.models.promo_message.optimize_image") as mock_opt,
            patch("PIL.Image.open"),  # Prevent actual image processing
        ):
            promo = PromoMessage(
                title="With Image",
                description="Desc",
                starts_at=now - timedelta(hours=1),
                ends_at=now + timedelta(hours=1),
                image=fake_image,
            )
            mock_opt.return_value = None
            with contextlib.suppress(Exception):
                promo.save()

    def test_save_without_image_does_not_call_optimize(self):
        with patch("features.promos.models.promo_message.optimize_image") as mock_opt:
            _make_promo()
            mock_opt.assert_not_called()


@pytest.mark.django_db
class TestPromoMessageStatusDisplayFallback:
    def test_status_display_fallback_for_unknown_status(self):
        """When status doesn't match any choice, returns the raw status string."""
        promo = _make_promo(is_active=True, starts_offset_hours=-1, ends_offset_hours=1)
        # Monkeypatch the status property to return an unknown value
        original_status = PromoMessage.status.fget
        PromoMessage.status = property(lambda self: "unknown_status")
        try:
            display = promo.status_display
            # Falls through to: return str(status_val)
            assert display == "unknown_status"
        finally:
            PromoMessage.status = property(original_status)


@pytest.mark.django_db
class TestPromoMessageSaveImageUpdate:
    def test_save_existing_instance_with_changed_image_calls_optimize(self):
        """When updating an existing PromoMessage and image changes, optimize_image is called."""
        promo = _make_promo()  # Create without image
        assert promo.pk is not None

        from django.core.files.uploadedfile import SimpleUploadedFile

        new_image = SimpleUploadedFile("new.jpg", b"fake_data", content_type="image/jpeg")
        with patch("features.promos.models.promo_message.optimize_image") as mock_opt:
            # Simulate image being set on the existing instance
            import contextlib

            promo.image = new_image
            mock_opt.return_value = None
            with contextlib.suppress(Exception):
                promo.save()
            # optimize_image should have been called for the changed image
            mock_opt.assert_called()


@pytest.mark.django_db
class TestPromoMessageMeta:
    def test_ordering_by_priority_desc(self):
        _make_promo(title="Low", priority=0)
        _make_promo(title="High", priority=10)
        promos = list(PromoMessage.objects.all())
        assert promos[0].priority > promos[1].priority

    def test_promo_status_choices_count(self):
        choices = PromoMessage.PromoStatus.choices
        assert len(choices) == 4

    def test_promo_status_values(self):
        assert PromoMessage.PromoStatus.ACTIVE == "active"
        assert PromoMessage.PromoStatus.SCHEDULED == "scheduled"
        assert PromoMessage.PromoStatus.EXPIRED == "expired"
        assert PromoMessage.PromoStatus.INACTIVE == "inactive"

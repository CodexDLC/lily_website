"""
API endpoints for promo messages.

Public endpoints (no authentication required):
- GET /active/ - Get active promo for current page
- POST /{id}/track-view/ - Track promo view
- POST /{id}/track-click/ - Track promo click
"""

from core.logger import log
from features.promos.models import PromoMessage
from features.promos.services import PromoService
from ninja import Router, Schema
from ninja.errors import HttpError

router = Router()  # Public router (no auth)


# ── Schemas ──


class PromoMessageResponse(Schema):
    """Response schema for active promo message."""

    id: int
    title: str
    description: str
    button_text: str
    button_color: str
    text_color: str
    display_delay: int
    image_url: str | None

    @staticmethod
    def from_promo_message(promo: PromoMessage, request) -> "PromoMessageResponse":
        """Convert PromoMessage model to response schema."""
        # Get the image URL if exists
        image_url = None
        if promo.image:
            # Build absolute URL
            image_url = request.build_absolute_uri(promo.image.url)

        return PromoMessageResponse(
            id=promo.id,
            title=promo.title,
            description=promo.description,
            button_text=promo.button_text,
            button_color=promo.button_color,
            text_color=promo.text_color,
            display_delay=promo.display_delay,
            image_url=image_url,
        )


class TrackResponse(Schema):
    """Response for tracking endpoints."""

    success: bool
    message: str


# ── Endpoints ──


@router.get("/active/", response={200: PromoMessageResponse, 404: dict})
def get_active_promo(request, page: str | None = None):
    """
    Get the currently active promo for a specific page.
    """
    log.debug(f"API: Promos | Action: GetActive | page={page}")
    promo = PromoService.get_active_promo(page_slug=page)

    if not promo:
        log.debug(f"API: Promos | Action: GetActive | status=NotFound | page={page}")
        return 404, {"detail": "No active promos"}

    log.info(f"API: Promos | Action: GetActive | status=Success | promo_id={promo.id} | page={page}")
    return 200, PromoMessageResponse.from_promo_message(promo, request)


@router.post("/{promo_id}/track-view/", response=TrackResponse)
def track_view(request, promo_id: int):
    """
    Track that a promo was viewed (floating button shown).
    """
    log.debug(f"API: Promos | Action: TrackView | promo_id={promo_id}")

    if not PromoService.is_promo_active(promo_id):
        log.warning(f"API: Promos | Action: TrackView | status=Failed | promo_id={promo_id} | reason=NotActive")
        raise HttpError(404, "Promo not found or not active")

    PromoService.track_view(promo_id)
    log.info(f"API: Promos | Action: TrackView | status=Success | promo_id={promo_id}")

    return TrackResponse(success=True, message="View tracked")


@router.post("/{promo_id}/track-click/", response=TrackResponse)
def track_click(request, promo_id: int):
    """
    Track that a promo was clicked (modal opened).
    """
    log.debug(f"API: Promos | Action: TrackClick | promo_id={promo_id}")

    if not PromoService.is_promo_active(promo_id):
        log.warning(f"API: Promos | Action: TrackClick | status=Failed | promo_id={promo_id} | reason=NotActive")
        raise HttpError(404, "Promo not found or not active")

    PromoService.track_click(promo_id)
    log.info(f"API: Promos | Action: TrackClick | status=Success | promo_id={promo_id}")

    return TrackResponse(success=True, message="Click tracked")

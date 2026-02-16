"""
API endpoints for promo promos.

Public endpoints (no authentication required):
- GET /active/ - Get active notification for current page
- POST /{id}/track-view/ - Track notification view
- POST /{id}/track-click/ - Track notification click
"""

from features.promos.models import PromoMessage
from features.promos.services import NotificationService
from ninja import Router, Schema
from ninja.errors import HttpError

router = Router()  # Public router (no auth)


# ── Schemas ──


class NotificationResponse(Schema):
    """Response schema for active notification."""

    id: int
    title: str
    description: str
    button_text: str
    button_color: str
    text_color: str
    display_delay: int
    image_url: str | None

    @staticmethod
    def from_notification(notification: PromoMessage, request) -> "NotificationResponse":
        """Convert PromoMessage model to response schema."""
        # Get the image URL if exists
        image_url = None
        if notification.image:
            # Build absolute URL
            image_url = request.build_absolute_uri(notification.image.url)

        return NotificationResponse(
            id=notification.id,
            title=notification.title,
            description=notification.description,
            button_text=notification.button_text,
            button_color=notification.button_color,
            text_color=notification.text_color,
            display_delay=notification.display_delay,
            image_url=image_url,
        )


class TrackResponse(Schema):
    """Response for tracking endpoints."""

    success: bool
    message: str


# ── Endpoints ──


@router.get("/active/", response={200: NotificationResponse, 404: dict})
def get_active_notification(request, page: str | None = None):
    """
    Get the currently active notification for a specific page.

    Args:
        page: Page slug (e.g., 'home', 'services', 'team'). Optional.

    Returns:
        NotificationResponse if active notification found, 404 otherwise.
    """
    notification = NotificationService.get_active_notification(page_slug=page)

    if not notification:
        return 404, {"detail": "No active promos"}

    return 200, NotificationResponse.from_notification(notification, request)


@router.post("/{notification_id}/track-view/", response=TrackResponse)
def track_view(request, notification_id: int):
    """
    Track that a notification was viewed (floating button shown).

    Args:
        notification_id: ID of the notification.

    Returns:
        TrackResponse with success status.
    """
    if not NotificationService.is_notification_active(notification_id):
        raise HttpError(404, "Notification not found or not active")

    NotificationService.track_view(notification_id)

    return TrackResponse(success=True, message="View tracked")


@router.post("/{notification_id}/track-click/", response=TrackResponse)
def track_click(request, notification_id: int):
    """
    Track that a notification was clicked (modal opened).

    Args:
        notification_id: ID of the notification.

    Returns:
        TrackResponse with success status.
    """
    if not NotificationService.is_notification_active(notification_id):
        raise HttpError(404, "Notification not found or not active")

    NotificationService.track_click(notification_id)

    return TrackResponse(success=True, message="Click tracked")

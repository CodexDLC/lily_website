from features.booking.api.bot import router as bot_router
from features.conversations.api import router as conversations_router

from .base import api
from .tracking import router as tracking_router

api.add_router("/bot", bot_router)
api.add_router("/v1/conversations", conversations_router)
api.add_router("/v1/tracking", tracking_router)

__all__ = ["api"]

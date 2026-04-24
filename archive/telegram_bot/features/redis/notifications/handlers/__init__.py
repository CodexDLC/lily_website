from .handlers import notifications_router
from .handlers import router as router

# Export for discovery service
redis_router = notifications_router

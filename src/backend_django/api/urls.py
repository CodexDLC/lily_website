"""
lily_website — API Configuration (Django Ninja).

Versioned API routers. Bot and external clients use these endpoints.
Docs: /api/docs
"""

from api.admin import router as admin_router
from api.booking import router as booking_router
from api.instance import api
from api.promos import router as promos_router
from ninja import Router

# from .stream_publisher import router as stream_publisher_router # ВРЕМЕННО ОТКЛЮЧЕНО

# ── v1 ──
v1 = Router()


@v1.get("/health")
def health(request):
    """Health check endpoint."""
    return {"status": "ok"}


# Добавляем роутер для публикации сообщений в стрим
# v1.add_router("/manager_redis/", stream_publisher_router) # ВРЕМЕННО ОТКЛЮЧЕНО

# Admin API (Dashboard, etc)
v1.add_router("/admin/", admin_router)

# Booking API для Telegram Bot (управление записями)
v1.add_router("/booking/", booking_router)

# Promos API (public, no auth)
v1.add_router("/promos/", promos_router)


api.add_router("/v1/", v1)

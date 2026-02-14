"""
lily_website — API Configuration (Django Ninja).

Versioned API routers. Bot and external clients use these endpoints.
Docs: /api/docs
"""

from api.instance import api
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


api.add_router("/v1/", v1)

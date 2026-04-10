from features.booking.api.bot import router as bot_router
from ninja import NinjaAPI

api = NinjaAPI(title="Lily API", version="2.0")

api.add_router("/bot", bot_router)


@api.get("/v1/health", tags=["System"])
def health_check(request):
    return {"status": "ok"}
